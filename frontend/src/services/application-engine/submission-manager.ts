import type { SubmissionResult } from './types'
import type { ProviderId } from '../discovery/types'
import { actionEngine } from '../browser/action-engine'
import { locatorEngine } from '../browser/locator-engine'
import { navigationEngine } from '../browser/navigation-engine'
import { errorRecoveryService } from '../browser/error-recovery'

export const submissionManager = {
  async submitForm(
    sessionId: string,
    submitSelector: string,
    providerId: ProviderId,
    applicationUrl: string
  ): Promise<SubmissionResult> {
    const startTime = Date.now()
    const errors: string[] = []

    const result = await errorRecoveryService.recoverAction(async () => {
      const submitButton = await locatorEngine.findElement(submitSelector, 'css')
      if (!submitButton) {
        errors.push('Submit button not found')
        return false
      }

      if (!submitButton.enabled) {
        errors.push('Submit button is disabled')
        return false
      }

      return await actionEngine.click(submitButton, sessionId)
    })

    if (!result && errors.length === 0) {
      errors.push('Submission action failed')
    }

    const duration = Date.now() - startTime

    let confirmationPage = false
    let confirmationMessage: string | null = null

    if (result) {
      try {
        await navigationEngine.waitForPageReady(5000)
        const confirmationElements = await locatorEngine.findElements(
          '.confirmation, .success-message, [data-testid="confirmation"], [role="alert"]',
          'css',
          { timeout: 3000 }
        )
        confirmationPage = confirmationElements.length > 0

        if (confirmationPage && confirmationElements[0]?.text) {
          confirmationMessage = confirmationElements[0].text
        }
      } catch {
        confirmationPage = false
      }
    }

    return {
      success: result,
      applicationUrl,
      confirmationPage,
      confirmationMessage,
      applicationId: result ? `app_${Date.now()}` : null,
      duration,
      errors,
      providerId,
      timestamp: new Date().toISOString(),
    }
  },

  async detectConfirmation(): Promise<{ confirmed: boolean; message: string | null }> {
    try {
      const confirmTexts = [
        'application submitted',
        'thank you',
        'we have received',
        'application received',
        'successfully applied',
        'your application has been',
      ]

      const bodyElements = await locatorEngine.findElements('body', 'css', { timeout: 2000 })
      const bodyText = bodyElements[0]?.text?.toLowerCase() ?? ''

      const matched = confirmTexts.find(t => bodyText.includes(t))
      return {
        confirmed: matched !== undefined,
        message: matched ?? null,
      }
    } catch {
      return { confirmed: false, message: null }
    }
  },
}
