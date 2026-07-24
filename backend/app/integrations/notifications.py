from __future__ import annotations

from app.integrations.schemas import NotificationTemplate

TEMPLATES: dict[str, NotificationTemplate] = {
    "job_discovered": NotificationTemplate(
        name="job_discovered",
        subject_template="New Job Found: {{position}} at {{company}}",
        body_template=(
            "A new job has been discovered matching your profile.\n\n"
            "Position: {{position}}\nCompany: {{company}}\n"
            "Location: {{location}}\n\nView details: {{job_url}}"
        ),
        html_template=(
            "<h2>New Job Found</h2><p>A new job has been discovered matching your profile.</p>"
            "<table><tr><td><strong>Position:</strong></td><td>{{position}}</td></tr>"
            "<tr><td><strong>Company:</strong></td><td>{{company}}</td></tr>"
            "<tr><td><strong>Location:</strong></td><td>{{location}}</td></tr></table>"
            "<p><a href='{{job_url}}'>View Job Details</a></p>"
        ),
        variables=["position", "company", "location", "job_url"],
    ),
    "job_matched": NotificationTemplate(
        name="job_matched",
        subject_template="Job Match: {{position}} at {{company}} ({{score}}% match)",
        body_template=(
            "A high-match job has been found.\n\nPosition: {{position}}\nCompany: {{company}}\n"
            "Match Score: {{score}}%\nLocation: {{location}}\n\nReview and apply: {{job_url}}"
        ),
        html_template=(
            "<h2>Job Match Found</h2><p><strong>{{position}}</strong> at <strong>{{company}}</strong>"
            " matches your profile with <strong>{{score}}%</strong>.</p>"
            "<p><a href='{{job_url}}'>Review and Apply</a></p>"
        ),
        variables=["position", "company", "score", "location", "job_url"],
    ),
    "application_prepared": NotificationTemplate(
        name="application_prepared",
        subject_template="Application Prepared for {{position}} at {{company}}",
        body_template=(
            "Your application has been prepared.\n\nPosition: {{position}}\n"
            "Company: {{company}}\n\nReview and submit: {{application_url}}"
        ),
        html_template=(
            "<h2>Application Prepared</h2><p>Your application for <strong>{{position}}</strong>"
            " at <strong>{{company}}</strong> is ready.</p>"
            "<p><a href='{{application_url}}'>Review and Submit</a></p>"
        ),
        variables=["position", "company", "application_url"],
    ),
    "application_submitted": NotificationTemplate(
        name="application_submitted",
        subject_template="Application Submitted: {{position}} at {{company}}",
        body_template=(
            "Your application has been submitted.\n\nPosition: {{position}}\nCompany: {{company}}\n"
            "Status: {{status}}\nSubmitted At: {{submitted_at}}\n\nTrack progress: {{tracking_url}}"
        ),
        html_template=(
            "<h2>Application Submitted</h2><p>Your application for <strong>{{position}}</strong>"
            " at <strong>{{company}}</strong> has been submitted.</p>"
            "<p><strong>Status:</strong> {{status}}</p>"
            "<p><a href='{{tracking_url}}'>Track Application</a></p>"
        ),
        variables=["position", "company", "status", "submitted_at", "tracking_url"],
    ),
    "application_failed": NotificationTemplate(
        name="application_failed",
        subject_template="Application Failed: {{position}} at {{company}}",
        body_template=(
            "Your application could not be submitted.\n\n"
            "Position: {{position}}\nCompany: {{company}}\n"
            "Error: {{error}}\n\nPlease review and try again."
        ),
        html_template=(
            "<h2>Application Failed</h2><p>Your application for <strong>{{position}}</strong>"
            " at <strong>{{company}}</strong> could not be submitted.</p>"
            "<p><strong>Error:</strong> {{error}}</p>"
        ),
        variables=["position", "company", "error"],
    ),
    "application_accepted": NotificationTemplate(
        name="application_accepted",
        subject_template="Application Accepted: {{position}} at {{company}}",
        body_template=(
            "Great news! Your application has been accepted.\n\n"
            "Position: {{position}}\nCompany: {{company}}\n\n"
            "Next steps may include interviews or assessments."
        ),
        html_template=(
            "<h2>Application Accepted</h2><p>Your application for <strong>{{position}}</strong>"
            " at <strong>{{company}}</strong> has been accepted!</p>"
        ),
        variables=["position", "company"],
    ),
    "application_rejected": NotificationTemplate(
        name="application_rejected",
        subject_template="Application Update: {{position}} at {{company}}",
        body_template=(
            "Your application status has been updated.\n\nPosition: {{position}}\n"
            "Company: {{company}}\nStatus: {{status}}\n\nKeep searching \u2014 new opportunities await."
        ),
        html_template=(
            "<h2>Application Status Update</h2><p>Your application for <strong>{{position}}</strong>"
            " at <strong>{{company}}</strong> status: <strong>{{status}}</strong>.</p>"
        ),
        variables=["position", "company", "status"],
    ),
    "workflow_completed": NotificationTemplate(
        name="workflow_completed",
        subject_template="Workflow Completed: {{workflow_name}}",
        body_template=(
            "A workflow has completed successfully.\n\nWorkflow: {{workflow_name}}\n"
            "Duration: {{duration}}\nStages Completed: {{stages_completed}}\n\nView report: {{report_url}}"
        ),
        html_template=(
            "<h2>Workflow Completed</h2><p><strong>{{workflow_name}}</strong>"
            " completed successfully in {{duration}}.</p>"
            "<p><a href='{{report_url}}'>View Report</a></p>"
        ),
        variables=["workflow_name", "duration", "stages_completed", "report_url"],
    ),
    "workflow_failed": NotificationTemplate(
        name="workflow_failed",
        subject_template="Workflow Failed: {{workflow_name}}",
        body_template=(
            "A workflow has failed.\n\nWorkflow: {{workflow_name}}\n"
            "Error: {{error}}\nStage: {{stage}}\n\nReview and retry: {{report_url}}"
        ),
        html_template=(
            "<h2>Workflow Failed</h2><p><strong>{{workflow_name}}</strong>"
            " failed at stage <strong>{{stage}}</strong>.</p>"
            "<p><strong>Error:</strong> {{error}}</p>"
            "<p><a href='{{report_url}}'>Review and Retry</a></p>"
        ),
        variables=["workflow_name", "error", "stage", "report_url"],
    ),
    "manual_intervention_required": NotificationTemplate(
        name="manual_intervention_required",
        subject_template="Manual Intervention Required: {{workflow_name}}",
        body_template=(
            "A workflow requires your attention.\n\nWorkflow: {{workflow_name}}\n"
            "Stage: {{stage}}\nReason: {{reason}}\n\nReview now: {{review_url}}"
        ),
        html_template=(
            "<h2>Manual Intervention Required</h2><p><strong>{{workflow_name}}</strong>"
            " needs your attention at stage <strong>{{stage}}</strong>.</p>"
            "<p><strong>Reason:</strong> {{reason}}</p>"
            "<p><a href='{{review_url}}'>Review Now</a></p>"
        ),
        variables=["workflow_name", "stage", "reason", "review_url"],
    ),
    "orchestration_paused": NotificationTemplate(
        name="orchestration_paused",
        subject_template="Orchestration Paused: {{orchestration_id}}",
        body_template=(
            "An orchestration has been paused.\n\n" "ID: {{orchestration_id}}\nStage: {{stage}}\nReason: {{reason}}"
        ),
        html_template=(
            "<h2>Orchestration Paused</h2><p>Orchestration <strong>{{orchestration_id}}</strong>"
            " paused at <strong>{{stage}}</strong>.</p><p>{{reason}}</p>"
        ),
        variables=["orchestration_id", "stage", "reason"],
    ),
    "orchestration_resumed": NotificationTemplate(
        name="orchestration_resumed",
        subject_template="Orchestration Resumed: {{orchestration_id}}",
        body_template="An orchestration has been resumed.\n\nID: {{orchestration_id}}\nStage: {{stage}}",
        html_template=(
            "<h2>Orchestration Resumed</h2><p>Orchestration <strong>{{orchestration_id}}</strong>"
            " resumed at <strong>{{stage}}</strong>.</p>"
        ),
        variables=["orchestration_id", "stage"],
    ),
    "report_generated": NotificationTemplate(
        name="report_generated",
        subject_template="Report Generated: {{report_name}}",
        body_template=(
            "A report has been generated.\n\nReport: {{report_name}}\nPeriod: {{period}}\n\n" "Download: {{report_url}}"
        ),
        html_template=(
            "<h2>Report Generated</h2><p><strong>{{report_name}}</strong> is ready.</p>"
            "<p><a href='{{report_url}}'>Download Report</a></p>"
        ),
        variables=["report_name", "period", "report_url"],
    ),
    "system_warning": NotificationTemplate(
        name="system_warning",
        subject_template="System Warning: {{component}}",
        body_template=(
            "A system warning has been detected.\n\n"
            "Component: {{component}}\nMessage: {{message}}\nSeverity: {{severity}}"
        ),
        html_template="<h2>System Warning</h2><p><strong>{{component}}</strong>: {{message}}</p>",
        variables=["component", "message", "severity"],
    ),
    "system_error": NotificationTemplate(
        name="system_error",
        subject_template="System Error: {{component}}",
        body_template=(
            "A system error has occurred.\n\n" "Component: {{component}}\nError: {{error}}\n\nAction required."
        ),
        html_template=(
            "<h2>System Error</h2><p><strong>{{component}}</strong> encountered an error.</p>"
            "<p><strong>{{error}}</strong></p>"
        ),
        variables=["component", "error"],
    ),
    "custom": NotificationTemplate(
        name="custom",
        subject_template="{{subject}}",
        body_template="{{body}}",
        html_template="<h2>{{subject}}</h2><p>{{body}}</p>",
        variables=["subject", "body"],
    ),
}


class NotificationTemplateService:
    def get(self, name: str) -> NotificationTemplate:
        template = TEMPLATES.get(name)
        if template is None:
            from app.integrations.exceptions import TemplateNotFoundError

            raise TemplateNotFoundError(f"Notification template '{name}' not found.")
        return template

    def list(self) -> list[str]:
        return list(TEMPLATES.keys())

    def render(self, template_name: str, variables: dict[str, str]) -> NotificationTemplate:
        template = self.get(template_name)
        rendered_subject = template.subject_template
        rendered_body = template.body_template
        rendered_html = template.html_template
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            rendered_subject = rendered_subject.replace(placeholder, value)
            rendered_body = rendered_body.replace(placeholder, value)
            if rendered_html:
                rendered_html = rendered_html.replace(placeholder, value)
        return NotificationTemplate(
            name=template.name,
            subject_template=rendered_subject,
            body_template=rendered_body,
            html_template=rendered_html,
            channel=template.channel,
            variables=template.variables,
        )
