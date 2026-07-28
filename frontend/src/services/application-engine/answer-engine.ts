import type { SemanticFieldCategory, AIAnswerRequest, AIAnswer, ProfileData } from './types'

interface AnswerTemplate {
  generate(request: AIAnswerRequest): string
}

const ANSWER_TEMPLATES: Record<string, AnswerTemplate> = {
  about_yourself: {
    generate(r) {
      const profile = r.profile
      const parts: string[] = []
      if (profile.headline) parts.push(profile.headline)
      parts.push(`I am a ${r.context.jobTitle} with experience in ${r.context.requiredSkills.slice(0, 5).join(', ')}.`)
      if (profile.currentCompany) parts.push(`I currently work at ${profile.currentCompany}.`)
      if (profile.yearsOfExperience) parts.push(`I have ${profile.yearsOfExperience} of experience.`)
      return parts.join(' ')
    },
  },
  why_company: {
    generate(r) {
      const desc = r.context.companyDescription
        ? `I am impressed by ${r.context.companyDescription} at ${r.context.companyName}`
        : `I am excited about the opportunity at ${r.context.companyName}`
      return `${desc}. I believe my skills in ${r.context.requiredSkills.slice(0, 4).join(', ')} align well with what your team is looking for, and I am eager to contribute to your continued success.`
    },
  },
  why_role: {
    generate(r) {
      return `The ${r.context.jobTitle} role at ${r.context.companyName} aligns perfectly with my career goals and expertise. I have developed strong skills in ${r.context.requiredSkills.slice(0, 3).join(', ')}, and I am excited to apply them to solve challenging problems in this position.`
    },
  },
  expected_salary: {
    generate(r) {
      if (r.profile.expectedSalary) return r.profile.expectedSalary
      return 'I am open to discussing compensation based on the role responsibilities and overall package.'
    },
  },
  current_salary: {
    generate(r) {
      if (r.profile.currentSalary) return r.profile.currentSalary
      return ''
    },
  },
  notice_period: {
    generate(r) {
      if (r.profile.noticePeriod) return r.profile.noticePeriod
      return 'I can provide my notice period details upon discussion.'
    },
  },
  work_authorization: {
    generate(r) {
      if (r.profile.workAuthorization) return r.profile.workAuthorization
      return 'I am authorized to work in the respective country.'
    },
  },
  visa_status: {
    generate(r) {
      if (r.profile.visaStatus) return r.profile.visaStatus
      return ''
    },
  },
  availability: {
    generate(_r) {
      return 'I am available to start immediately.'
    },
  },
  strengths: {
    generate(r) {
      const skills = r.context.requiredSkills.slice(0, 3)
      return `My key strengths include ${skills.join(', ')}. I am a quick learner, detail-oriented, and thrive in collaborative environments. I bring strong problem-solving abilities and a commitment to delivering high-quality work.`
    },
  },
  weaknesses: {
    generate(_r) {
      return 'I sometimes focus deeply on details, which has helped me produce high-quality work. I have been working on balancing this by setting clear priorities and time-boxing tasks to maintain efficiency.'
    },
  },
  leadership: {
    generate(_r) {
      return 'I have experience leading projects and mentoring team members. I believe in leading by example and fostering a collaborative environment where everyone can contribute their best work.'
    },
  },
  conflict_resolution: {
    generate(_r) {
      return 'When conflicts arise, I focus on understanding all perspectives first. I believe in open communication and finding common ground to reach a solution that works for the team. I have successfully resolved disagreements by facilitating constructive discussions.'
    },
  },
  career_goals: {
    generate(r) {
      return `My career goal is to grow as a ${r.context.jobTitle} and take on increasing responsibilities. I want to deepen my expertise in ${r.context.requiredSkills.slice(0, 2).join(', ')} and eventually mentor other team members while contributing to impactful projects at ${r.context.companyName}.`
    },
  },
  relocation: {
    generate(_r) {
      return 'I am open to relocation for the right opportunity.'
    },
  },
  remote_work: {
    generate(_r) {
      return 'I have experience working remotely and am comfortable with remote collaboration tools.'
    },
  },
}

function inferQuestionCategory(question: string): SemanticFieldCategory {
  const q = question.toLowerCase()
  if (q.includes('tell us about yourself') || q.includes('introduce yourself')) return 'bio' as SemanticFieldCategory
  if (q.includes('why do you want to work') || q.includes('why are you interested')) return 'bio' as SemanticFieldCategory
  if (q.includes('strength')) return 'bio' as SemanticFieldCategory
  if (q.includes('weakness')) return 'bio' as SemanticFieldCategory
  if (q.includes('salary')) return 'expected_salary'
  if (q.includes('notice')) return 'notice_period'
  if (q.includes('available') || q.includes('start')) return 'bio' as SemanticFieldCategory
  if (q.includes('relocate')) return 'bio' as SemanticFieldCategory
  if (q.includes('remote')) return 'bio' as SemanticFieldCategory
  if (q.includes('visa') || q.includes('work authorization')) return 'work_authorization'
  if (q.includes('goal') || q.includes('career')) return 'bio' as SemanticFieldCategory
  if (q.includes('leadership')) return 'bio' as SemanticFieldCategory
  if (q.includes('conflict')) return 'bio' as SemanticFieldCategory
  return 'custom'
}

function findMatchingTemplateKey(question: string): string | null {
  const q = question.toLowerCase()
  if (q.includes('yourself') || q.includes('introduce') || q.includes('about you')) return 'about_yourself'
  if (q.includes('why') && (q.includes('company') || q.includes('work') || q.includes('interest'))) return 'why_company'
  if (q.includes('why') && (q.includes('role') || q.includes('position') || q.includes('this job'))) return 'why_role'
  if (q.includes('salary') && q.includes('expect')) return 'expected_salary'
  if (q.includes('current salary')) return 'current_salary'
  if (q.includes('notice')) return 'notice_period'
  if (q.includes('strength')) return 'strengths'
  if (q.includes('weakness')) return 'weaknesses'
  if (q.includes('leadership')) return 'leadership'
  if (q.includes('conflict')) return 'conflict_resolution'
  if (q.includes('goal') || q.includes('career')) return 'career_goals'
  if (q.includes('available') || q.includes('start when') || q.includes('start date')) return 'availability'
  if (q.includes('relocate')) return 'relocation'
  if (q.includes('remote')) return 'remote_work'
  if (q.includes('authorization') || q.includes('visa') || q.includes('work right')) return 'work_authorization'
  return null
}

export const answerEngine = {
  generateAnswer(request: AIAnswerRequest): AIAnswer {
    const templateKey = findMatchingTemplateKey(request.question)
    if (templateKey && ANSWER_TEMPLATES[templateKey]) {
      const answer = ANSWER_TEMPLATES[templateKey].generate(request)
      return { answer, confidence: 0.8, generated: true }
    }

    if (request.fieldCategory !== 'custom') {
      const categoryKey = request.fieldCategory.replace(/-/g, '_')
      if (ANSWER_TEMPLATES[categoryKey]) {
        const answer = ANSWER_TEMPLATES[categoryKey].generate(request)
        return { answer, confidence: 0.7, generated: true }
      }
    }

    return { answer: `Please provide your response regarding: ${request.question}`, confidence: 0.1, generated: false }
  },

  generateAnswers(questions: { fieldId: string; question: string; category: SemanticFieldCategory }[], context: AIAnswerRequest['context'], profile: ProfileData): Map<string, AIAnswer> {
    const answers = new Map<string, AIAnswer>()
    for (const q of questions) {
      const request: AIAnswerRequest = {
        fieldCategory: q.category,
        question: q.question,
        context,
        profile,
      }
      answers.set(q.fieldId, this.generateAnswer(request))
    }
    return answers
  },

  inferQuestionCategory(question: string): SemanticFieldCategory {
    return inferQuestionCategory(question)
  },
}
