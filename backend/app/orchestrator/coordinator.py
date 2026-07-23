from __future__ import annotations

import asyncio

import structlog

from app.orchestrator.exceptions import StageExecutionError
from app.orchestrator.interfaces import PipelineStageExecutor
from app.orchestrator.schemas import OrchestrationContext, PipelineStage

logger = structlog.get_logger(__name__)


class ProfileIntelligenceExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.PROFILE_INTELLIGENCE

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.profile is not None or context.user_id is None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.profile_intelligence.dependencies import get_profile_intelligence_service
        session = context.metadata.get("db_session")
        if session is None:
            context.warnings.append("ProfileIntelligence skipped: no db_session in metadata")
            context.mark_stage_skipped(self.stage(), "No database session available")
            return context
        try:
            svc = get_profile_intelligence_service(session)
            loop = asyncio.get_event_loop()
            profile = loop.run_until_complete(svc.get_profile_intelligence(context.user_id))
            context.profile = profile
            context.set_stage_output(self.stage(), profile)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class JobDiscoveryExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.JOB_DISCOVERY

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.job is not None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.jobs.dependencies import get_job_discovery_service
        from app.jobs.schemas import JobSearchRequest
        try:
            jds = get_job_discovery_service()
            request = JobSearchRequest(
                query=context.metadata.get("search_query", ""),
                keywords=context.metadata.get("search_keywords", []),
                location=context.metadata.get("search_location", ""),
                limit=context.metadata.get("search_limit", 10),
            )
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(jds.search(request))
            context.matched_jobs = response.results
            context.set_stage_output(self.stage(), response)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class JobMatchingExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.JOB_MATCHING

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.match_result is not None or context.profile is None or context.job is None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.job_matching.dependencies import get_job_matching_service
        try:
            jms = get_job_matching_service()
            match_result = jms.match(profile=context.profile, job=context.job)
            context.match_result = match_result
            context.set_stage_output(self.stage(), match_result)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class ApplicationIntelligenceExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.APPLICATION_INTELLIGENCE

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.application_intelligence is not None or context.job is None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.application_intelligence.dependencies import get_application_intelligence_service
        try:
            ais = get_application_intelligence_service()
            ai_result = ais.analyze(
                job=context.job,
                match_result=context.match_result,
                profile_intelligence=context.profile,
            )
            context.application_intelligence = ai_result
            context.set_stage_output(self.stage(), ai_result)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class ResumeOptimizationExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.RESUME_OPTIMIZATION

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.optimized_resume is not None or context.profile is None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.resume_optimization.dependencies import get_resume_optimization_service
        try:
            ros = get_resume_optimization_service()
            optimized = ros.optimize(
                resume=context.metadata.get("resume"),
                job_posting=context.job,
                profile=context.profile,
                match_result=context.match_result,
            )
            context.optimized_resume = optimized
            context.set_stage_output(self.stage(), optimized)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class CoverLetterExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.COVER_LETTER

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.generated_cover_letter is not None or context.profile is None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.cover_letter.dependencies import get_cover_letter_service
        try:
            cls_svc = get_cover_letter_service()
            cover = cls_svc.generate(
                profile=context.profile,
                job_posting=context.job,
                optimized_resume=context.optimized_resume,
                match_result=context.match_result,
            )
            context.generated_cover_letter = cover
            context.set_stage_output(self.stage(), cover)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class ApplicationPackageExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.APPLICATION_PACKAGE

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.application_package is not None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.application_package.dependencies import get_application_package_service
        try:
            aps = get_application_package_service()
            package = aps.generate(
                job_posting=context.job,
                profile_intelligence=context.profile,
                application_intelligence=context.application_intelligence,
                match_result=context.match_result,
                optimized_resume=context.optimized_resume,
                generated_cover_letter=context.generated_cover_letter,
            )
            context.application_package = package
            context.set_stage_output(self.stage(), package)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class ReviewExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.REVIEW

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.review_record is not None or context.application_package is None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.review.dependencies import get_review_service
        try:
            rs = get_review_service()
            package_id = getattr(context.application_package, "id", None) or context.orchestration_id
            rs.create_review(
                package_id=package_id,
                workflow_id=context.workflow_id,
                tracking_id=context.tracking_id,
            )
            context.review_id = package_id
            auto = rs.auto_approve(
                package_id=package_id,
                package=context.application_package,
                match_score=getattr(context.match_result, "overall_match_score", None),
            )
            context.review_record = auto
            context.set_stage_output(self.stage(), auto)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class WorkflowExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.WORKFLOW

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.workflow_id is not None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.workflow.dependencies import get_workflow_service
        from app.workflow.schemas import WorkflowState
        try:
            ws = get_workflow_service()
            wf_id = context.workflow_id or context.orchestration_id
            ws.create_workflow(wf_id, metadata={"orchestration_id": context.orchestration_id})
            ws.transition(wf_id, WorkflowState.PACKAGE_GENERATED, actor="orchestrator",
                           reason="Application package generated")
            if context.review_record:
                ws.transition(wf_id, WorkflowState.APPROVED, actor="orchestrator",
                              reason="Review completed")
            context.workflow_id = wf_id
            context.set_stage_output(self.stage(), wf_id)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class ATSDetectionExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.ATS_DETECTION

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.ats_result is not None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.ats.dependencies import get_ats_service
        try:
            ats = get_ats_service()
            job_url = getattr(context.job, "apply_url", None) or getattr(context.job, "url", None)
            if job_url:
                result = ats.detect(job_url)
                context.ats_result = result
            context.set_stage_output(self.stage(), context.ats_result)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class FormIntelligenceExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.FORM_INTELLIGENCE

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.form_analysis is not None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.forms.dependencies import get_forms_service
        try:
            fs = get_forms_service()
            job_url = getattr(context.job, "apply_url", None) or getattr(context.job, "url", None)
            page = context.metadata.get("page")
            if job_url and page:
                response = fs.analyze_and_plan(page=page, url=job_url,
                                               application_package=context.application_package)
                context.form_analysis = response.analysis
                context.execution_plan = response.plan
            context.set_stage_output(self.stage(), context.form_analysis)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class UploadExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.UPLOAD

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return len(context.upload_results) > 0

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.uploads.dependencies import get_uploads_service
        try:
            us = get_uploads_service()
            page = context.metadata.get("page")
            if context.execution_plan and page:
                plan = us.create_upload_plan(execution_plan=context.execution_plan,
                                             application_package=context.application_package)
                context.upload_plan = plan
                results = us.execute_upload_plan(page=page, plan=plan)
                context.upload_results = results
            context.set_stage_output(self.stage(), context.upload_results)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class SubmissionExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.SUBMISSION

    def is_skippable(self) -> bool:
        return True

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.submission_report is not None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.submission_engine.dependencies import get_submission_engine_service
        from app.submission_engine.schemas import ExecutionMode as SEMode
        try:
            ses = get_submission_engine_service()
            mode = SEMode.DRY_RUN if context.execution_mode.value == "dry_run" else SEMode.AUTOMATIC
            report = ses.execute_submission(
                page=context.metadata.get("page"),
                execution_plan=context.execution_plan,
                upload_plan=context.upload_plan,
                mode=mode,
            )
            context.submission_report = report
            context.set_stage_output(self.stage(), report)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context


class TrackingExecutor(PipelineStageExecutor):
    def stage(self) -> PipelineStage:
        return PipelineStage.TRACKING

    def is_skippable(self) -> bool:
        return False

    def should_skip(self, context: OrchestrationContext) -> bool:
        return context.tracking_record is not None

    def execute(self, context: OrchestrationContext) -> OrchestrationContext:
        from app.application_tracking.dependencies import get_application_tracking_service
        from app.application_tracking.schemas import ApplicationStatus, TimelineEventType
        try:
            ats_svc = get_application_tracking_service()
            track_id = context.tracking_id or context.orchestration_id
            record = ats_svc.create(track_id, metadata={
                "orchestration_id": context.orchestration_id,
                "job_id": str(getattr(context.job, "id", "")),
            })
            if context.submission_report:
                sub_status = getattr(context.submission_report, "status", "")
                status = ApplicationStatus.SUBMITTED if sub_status == "completed" else ApplicationStatus.QUEUED
                ats_svc.update_status(track_id, status, actor="orchestrator",
                                      reason="Submission completed")
                if getattr(context.submission_report, "confirmation_number", None):
                    ats_svc.add_event(track_id, TimelineEventType.SUBMITTED, actor="orchestrator",
                                      reason=f"Confirmed: {context.submission_report.confirmation_number}")
            context.tracking_id = track_id
            context.tracking_record = record
            context.set_stage_output(self.stage(), record)
        except Exception as e:
            raise StageExecutionError(self.stage().value, str(e), recoverable=True) from e
        return context
