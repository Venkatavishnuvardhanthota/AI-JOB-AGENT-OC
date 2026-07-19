import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.browser_automation import BrowserAutomationLog
from app.services.browser.base import BaseBrowserClient
from app.services.browser.form_filler import FormFiller
from app.services.browser.site_configs import get_site_config
from app.services.browser.types import (
    AutomationResult,
    ConsentStatus,
    SiteConfig,
    StepResult,
)

logger = logging.getLogger(__name__)


class BrowserAutomationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._max_retries = settings.PROVIDER_MAX_RETRIES

    async def run_automation(
        self,
        user_id: uuid.UUID,
        url: str,
        fields: list[dict],
        resume_file_path: str | None = None,
        cover_letter_file_path: str | None = None,
        certificate_file_paths: list[str] | None = None,
        job_posting_id: uuid.UUID | None = None,
    ) -> AutomationResult:
        site_config = get_site_config(url)
        if site_config and site_config.consent_status == ConsentStatus.NOT_PERMITTED:
            logger.warning("Automation not permitted for %s", url)
            return AutomationResult(
                success=False,
                status="failed",
                error=f"Browser automation is not permitted for {site_config.name}",
            )

        log_entry = BrowserAutomationLog(
            user_id=user_id,
            job_posting_id=job_posting_id,
            url=url,
            site_name=site_config.name if site_config else None,
            status="running",
            is_consent_verified=site_config is not None
            and site_config.consent_status == ConsentStatus.PERMITTED,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(log_entry)
        await self.session.flush()

        attempt = 0
        last_error = None
        all_steps: list[StepResult] = []
        all_screenshots: list[str] = []

        while attempt <= self._max_retries:
            client = self._create_client()
            try:
                await client.start()
                result = await self._execute_run(
                    client, url, fields, site_config,
                    resume_file_path, cover_letter_file_path,
                    certificate_file_paths or [],
                )
                all_steps.extend(result.steps)
                all_screenshots.extend(result.screenshot_paths)

                if result.success:
                    log_entry.status = "success"
                    log_entry.completed_at = datetime.now(timezone.utc)
                    log_entry.steps = [s.__dict__ for s in all_steps]
                    log_entry.screenshot_paths = all_screenshots
                    log_entry.retry_count = attempt
                    await self.session.flush()
                    return result

                last_error = result.error
                logger.warning(
                    "Automation attempt %d/%d failed: %s",
                    attempt + 1, self._max_retries + 1, last_error,
                )
            except Exception as e:
                last_error = str(e)
                logger.error(
                    "Automation attempt %d/%d error: %s",
                    attempt + 1, self._max_retries + 1, last_error,
                )
                ss = await self._safe_screenshot(client, f"error_attempt_{attempt}")
                if ss:
                    all_screenshots.append(ss)
            finally:
                await self._safe_close(client)

            attempt += 1
            if attempt <= self._max_retries:
                wait = 2 ** attempt
                logger.info("Retrying in %ds...", wait)
                await self._sleep(wait)

        log_entry.status = "failed"
        log_entry.error_message = last_error
        log_entry.completed_at = datetime.now(timezone.utc)
        log_entry.steps = [s.__dict__ for s in all_steps]
        log_entry.screenshot_paths = all_screenshots
        log_entry.retry_count = attempt
        await self.session.flush()

        return AutomationResult(
            success=False,
            status="failed",
            steps=all_steps,
            error=last_error,
            screenshot_paths=all_screenshots,
            retry_count=attempt,
        )

    async def get_log(self, log_id: uuid.UUID, user_id: uuid.UUID) -> BrowserAutomationLog | None:
        stmt = select(BrowserAutomationLog).where(
            BrowserAutomationLog.id == log_id,
            BrowserAutomationLog.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_logs(self, user_id: uuid.UUID) -> list[BrowserAutomationLog]:
        stmt = (
            select(BrowserAutomationLog)
            .where(BrowserAutomationLog.user_id == user_id)
            .order_by(BrowserAutomationLog.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _execute_run(
        self,
        client: BaseBrowserClient,
        url: str,
        fields: list[dict],
        site_config: SiteConfig | None,
        resume_path: str | None,
        cover_letter_path: str | None,
        certificate_paths: list[str],
    ) -> AutomationResult:
        steps: list[StepResult] = []
        screenshots: list[str] = []

        nav_ss = await client.take_screenshot("before_navigation")
        if nav_ss:
            screenshots.append(nav_ss)

        nav_start = time.monotonic()
        try:
            await client.navigate(url)
            nav_ok = True
        except Exception as e:
            nav_ok = False
            nav_error = str(e)
        nav_elapsed = int((time.monotonic() - nav_start) * 1000)

        steps.append(StepResult(
            step_name="navigate",
            success=nav_ok,
            duration_ms=nav_elapsed,
            error=None if nav_ok else nav_error,
        ))
        if not nav_ok:
            return AutomationResult(
                success=False, status="failed",
                steps=steps, error=nav_error,
                screenshot_paths=screenshots,
            )

        after_nav_ss = await client.take_screenshot("after_navigation")
        if after_nav_ss:
            screenshots.append(after_nav_ss)

        if site_config:
            await self._sleep(site_config.wait_after_navigation)

        filler = FormFiller(client)

        fill_results = await filler.fill_form(fields, site_config)
        steps.extend(fill_results)

        after_fill_ss = await client.take_screenshot("after_fill")
        if after_fill_ss:
            screenshots.append(after_fill_ss)

        upload_selectors = self._resolve_upload_selectors(site_config)

        if resume_path and upload_selectors.get("resume"):
            result = await filler.upload_resume(upload_selectors["resume"], resume_path)
            steps.append(result)

        if cover_letter_path and upload_selectors.get("cover_letter"):
            result = await filler.upload_cover_letter(
                upload_selectors["cover_letter"], cover_letter_path,
            )
            steps.append(result)

        for _i, cert_path in enumerate(certificate_paths):
            sel = upload_selectors.get("certificate")
            if sel:
                result = await filler.upload_certificate(sel, cert_path)
                steps.append(result)

        submit_selector = self._resolve_submit_selector(site_config)
        if submit_selector:
            submit_result = await filler.click_submit(submit_selector)
            steps.append(submit_result)

            after_submit_ss = await client.take_screenshot("after_submit")
            if after_submit_ss:
                screenshots.append(after_submit_ss)

        has_failure = any(not s.success for s in steps)
        status = "failed" if has_failure else "success"

        return AutomationResult(
            success=not has_failure,
            status=status,
            steps=steps,
            screenshot_paths=screenshots,
        )

    @staticmethod
    def _resolve_upload_selectors(site_config: SiteConfig | None) -> dict:
        if not site_config:
            return {}
        selectors: dict = {}
        if site_config.resume_upload_selector:
            selectors["resume"] = site_config.resume_upload_selector
        if site_config.cover_letter_upload_selector:
            selectors["cover_letter"] = site_config.cover_letter_upload_selector
        if site_config.certificate_upload_selector:
            selectors["certificate"] = site_config.certificate_upload_selector
        return selectors

    @staticmethod
    def _resolve_submit_selector(site_config: SiteConfig | None) -> str | None:
        if site_config and site_config.submit_button_selector:
            return site_config.submit_button_selector
        return "button[type='submit']"

    @staticmethod
    def _create_client() -> BaseBrowserClient:
        from app.services.browser.playwright_client import PlaywrightBrowserClient

        return PlaywrightBrowserClient()

    @staticmethod
    async def _safe_screenshot(client, name: str) -> str | None:
        try:
            if client:
                return await client.take_screenshot(name)
        except Exception:
            return None

    @staticmethod
    async def _safe_close(client) -> None:
        try:
            if client:
                await client.close()
        except Exception:
            pass

    @staticmethod
    async def _sleep(seconds: float) -> None:
        import asyncio

        await asyncio.sleep(seconds)
