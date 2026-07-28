import type { DetectedForm, DetectedField, MultiStepState, MultiStepInfo } from './types'
import { fieldDetector } from './field-detector'

export const multiStepCoordinator = {
  analyzeSteps(form: DetectedForm): MultiStepState {
    const steps: MultiStepInfo[] = []

    if (!form.isMultiStep || !form.totalSteps) {
      steps.push({
        index: 1,
        label: 'Form',
        fields: form.fields.map(f => f.id),
        completed: false,
      })

      return {
        detected: false,
        totalSteps: 1,
        currentStep: 1,
        steps,
        completedSteps: [],
      }
    }

    for (let i = 1; i <= form.totalSteps; i++) {
      const stepFields = fieldDetector.getFieldsByStep(form, i)
      steps.push({
        index: i,
        label: form.stepIndicators[i - 1] ?? `Step ${i}`,
        fields: stepFields.map(f => f.id),
        completed: false,
      })
    }

    return {
      detected: true,
      totalSteps: form.totalSteps,
      currentStep: form.currentStep ?? 1,
      steps,
      completedSteps: [],
    }
  },

  getCurrentStepFields(form: DetectedForm, state: MultiStepState): DetectedField[] {
    return form.fields.filter(f => f.stepIndex === state.currentStep || f.stepIndex === null)
  },

  isLastStep(state: MultiStepState): boolean {
    return state.currentStep >= state.totalSteps
  },

  isFirstStep(state: MultiStepState): boolean {
    return state.currentStep <= 1
  },

  markStepCompleted(state: MultiStepState, stepIndex: number): MultiStepState {
    const updatedSteps = state.steps.map(s =>
      s.index === stepIndex ? { ...s, completed: true } : s
    )
    return {
      ...state,
      steps: updatedSteps,
      completedSteps: [...new Set([...state.completedSteps, stepIndex])],
    }
  },

  advanceStep(state: MultiStepState): MultiStepState {
    const nextStep = Math.min(state.currentStep + 1, state.totalSteps)
    return { ...state, currentStep: nextStep }
  },

  goBackStep(state: MultiStepState): MultiStepState {
    const prevStep = Math.max(state.currentStep - 1, 1)
    return { ...state, currentStep: prevStep }
  },

  allStepsCompleted(state: MultiStepState): boolean {
    return state.completedSteps.length >= state.totalSteps
  },

  getStepProgress(state: MultiStepState): number {
    return Math.round((state.completedSteps.length / state.totalSteps) * 100)
  },
}
