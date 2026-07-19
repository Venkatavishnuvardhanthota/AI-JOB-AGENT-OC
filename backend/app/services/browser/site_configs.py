"""Site-specific automation configurations.
Only includes sites where browser automation is permitted by terms of service."""

from app.services.browser.types import (
    ConsentStatus,
    FormFieldType,
    SiteConfig,
    SiteFieldConfig,
)

PERMITTED_SITES: dict[str, SiteConfig] = {
    "greenhouse": SiteConfig(
        name="greenhouse",
        url_pattern="boards.greenhouse.io",
        consent_status=ConsentStatus.PERMITTED,
        fields=[
            SiteFieldConfig(
                selector="input[name='first_name']",
                field_type=FormFieldType.TEXT,
                required=True,
                label="First Name",
            ),
            SiteFieldConfig(
                selector="input[name='last_name']",
                field_type=FormFieldType.TEXT,
                required=True,
                label="Last Name",
            ),
            SiteFieldConfig(
                selector="input[name='email']",
                field_type=FormFieldType.TEXT,
                required=True,
                label="Email",
            ),
            SiteFieldConfig(
                selector="input[name='phone']",
                field_type=FormFieldType.TEXT,
                required=False,
                label="Phone",
            ),
            SiteFieldConfig(
                selector="textarea[name='cover_letter']",
                field_type=FormFieldType.TEXTAREA,
                required=False,
                label="Cover Letter",
            ),
        ],
        resume_upload_selector="input[name='resume']",
        cover_letter_upload_selector=None,
        certificate_upload_selector=None,
        submit_button_selector="button[type='submit']",
        login_required=False,
        supports_file_upload=True,
        wait_after_navigation=3.0,
        wait_after_action=1.0,
    ),
    "lever": SiteConfig(
        name="lever",
        url_pattern="jobs.lever.co",
        consent_status=ConsentStatus.PERMITTED,
        fields=[
            SiteFieldConfig(
                selector="input[name='name']",
                field_type=FormFieldType.TEXT,
                required=True,
                label="Full Name",
            ),
            SiteFieldConfig(
                selector="input[name='email']",
                field_type=FormFieldType.TEXT,
                required=True,
                label="Email",
            ),
            SiteFieldConfig(
                selector="input[name='phone']",
                field_type=FormFieldType.TEXT,
                required=False,
                label="Phone",
            ),
            SiteFieldConfig(
                selector="textarea[name='comments']",
                field_type=FormFieldType.TEXTAREA,
                required=False,
                label="Comments",
            ),
            SiteFieldConfig(
                selector="input[name='urls[LinkedIn]']",
                field_type=FormFieldType.TEXT,
                required=False,
                label="LinkedIn URL",
            ),
        ],
        resume_upload_selector="input[name='resume']",
        cover_letter_upload_selector=None,
        certificate_upload_selector=None,
        submit_button_selector="button[type='submit']",
        login_required=False,
        supports_file_upload=True,
        wait_after_navigation=3.0,
        wait_after_action=1.0,
    ),
    "ashby": SiteConfig(
        name="ashby",
        url_pattern="jobs.ashbyhq.com",
        consent_status=ConsentStatus.PERMITTED,
        fields=[
            SiteFieldConfig(
                selector="input[name='name']",
                field_type=FormFieldType.TEXT,
                required=True,
                label="Full Name",
            ),
            SiteFieldConfig(
                selector="input[name='email']",
                field_type=FormFieldType.TEXT,
                required=True,
                label="Email",
            ),
            SiteFieldConfig(
                selector="input[name='phone']",
                field_type=FormFieldType.TEXT,
                required=False,
                label="Phone",
            ),
        ],
        resume_upload_selector="input[type='file']",
        cover_letter_upload_selector=None,
        certificate_upload_selector=None,
        submit_button_selector="button[type='submit']",
        login_required=False,
        supports_file_upload=True,
        wait_after_navigation=3.0,
        wait_after_action=1.0,
    ),
}


def get_site_config(url: str) -> SiteConfig | None:
    for config in PERMITTED_SITES.values():
        if config.url_pattern in url:
            return config
    return None


def list_permitted_sites() -> list[dict]:
    return [
        {
            "site_name": cfg.name,
            "consent_status": cfg.consent_status.value,
            "url_pattern": cfg.url_pattern,
            "field_selectors": [f.selector for f in cfg.fields],
            "supports_file_upload": cfg.supports_file_upload,
        }
        for cfg in PERMITTED_SITES.values()
    ]
