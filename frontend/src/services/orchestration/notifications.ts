export interface NotificationPayload {
  title: string
  body: string
  url?: string
  metadata?: Record<string, string>
}

export const orchestrationNotificationService = {
  approvalRequired(workflowId: string, jobTitle: string, company: string): NotificationPayload {
    return { title: 'Approval Required', body: `Workflow for ${jobTitle} at ${company} needs your approval.`, url: `/orchestration/${workflowId}`, metadata: { workflowId, type: 'approval' } }
  },

  workflowStarted(workflowId: string, jobTitle: string, company: string): NotificationPayload {
    return { title: 'Workflow Started', body: `Application workflow started for ${jobTitle} at ${company}.`, url: `/orchestration/${workflowId}`, metadata: { workflowId, type: 'started' } }
  },

  submissionComplete(workflowId: string, jobTitle: string, company: string): NotificationPayload {
    return { title: 'Application Submitted', body: `Application for ${jobTitle} at ${company} has been submitted.`, url: `/orchestration/${workflowId}`, metadata: { workflowId, type: 'submitted' } }
  },

  workflowFailed(workflowId: string, jobTitle: string, company: string, error: string): NotificationPayload {
    return { title: 'Workflow Failed', body: `Application for ${jobTitle} at ${company} failed: ${error}`, url: `/orchestration/${workflowId}`, metadata: { workflowId, type: 'failed' } }
  },

  recoveryPerformed(workflowId: string, jobTitle: string, company: string): NotificationPayload {
    return { title: 'Recovery Performed', body: `Workflow for ${jobTitle} at ${company} has been recovered.`, url: `/orchestration/${workflowId}`, metadata: { workflowId, type: 'recovery' } }
  },

  retryScheduled(workflowId: string, jobTitle: string, company: string, attempt: number): NotificationPayload {
    return { title: 'Retry Scheduled', body: `Retry #${attempt} for ${jobTitle} at ${company}.`, url: `/orchestration/${workflowId}`, metadata: { workflowId, type: 'retry' } }
  },
}
