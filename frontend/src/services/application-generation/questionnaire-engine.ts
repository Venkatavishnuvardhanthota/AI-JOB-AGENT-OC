import type { QuestionnaireAnswer, QuestionnaireTopic, GenerationRequest } from './types'

const QUESTIONNAIRE_TEMPLATES: Record<QuestionnaireTopic, (req: GenerationRequest) => { question: string; generate: () => string }> = {
  about_yourself: (req) => ({
    question: 'Tell us about yourself and your background.',
    generate: () => generateAboutYourself(req),
  }),
  why_company: (req) => ({
    question: `Why do you want to work at ${req.companyName}?`,
    generate: () => generateWhyCompany(req),
  }),
  why_role: (req) => ({
    question: `Why are you interested in the ${req.jobTitle} role?`,
    generate: () => generateWhyRole(req),
  }),
  expected_salary: (req) => ({
    question: 'What are your salary expectations?',
    generate: () => generateSalary(req),
  }),
  notice_period: () => ({
    question: 'What is your notice period?',
    generate: () => 'My notice period is 2 weeks and I am flexible to negotiate based on the start date requirements.',
  }),
  work_authorization: () => ({
    question: 'Are you authorized to work in this country?',
    generate: () => 'Yes, I am fully authorized to work in this country without any restrictions or sponsorship requirements.',
  }),
  availability: () => ({
    question: 'When can you start?',
    generate: () => 'I am available to start within 2 weeks of acceptance, and can be flexible to accommodate your onboarding schedule.',
  }),
  leadership: () => ({
    question: 'Describe your leadership style.',
    generate: () => 'My leadership style is collaborative and empowerment-focused. I believe in setting clear vision and goals, then providing team members with the autonomy and support they need to excel. I regularly practice active listening, foster psychological safety, and lead by example through technical excellence.'
  }),
  conflict_resolution: () => ({
    question: 'How do you handle conflict in the workplace?',
    generate: () => 'I approach conflict directly and constructively by first understanding all perspectives through active listening. I focus on the issue rather than the person, seek common ground, and work toward a solution that aligns with team and company goals. I believe healthy debate leads to better outcomes when managed respectfully.',
  }),
  strengths: () => ({
    question: 'What are your greatest strengths?',
    generate: () => generateStrengths(),
  }),
  weaknesses: () => ({
    question: 'What are your areas for improvement?',
    generate: () => generateWeaknesses(),
  }),
  career_goals: (req) => ({
    question: 'What are your career goals?',
    generate: () => `My short-term goal is to contribute meaningfully as a ${req.jobTitle}, applying my skills to solve complex challenges at ${req.companyName}. In the long term, I aspire to grow into a technical leadership role where I can mentor others and drive architectural decisions that shape the direction of the products I work on.`,
  }),
  behavioral: () => ({
    question: 'Tell us about a challenging project you worked on.',
    generate: () => 'I worked on a complex migration project that involved moving a monolithic application to a microservices architecture. The challenge was maintaining zero downtime while transitioning. I coordinated with multiple teams, established incremental migration milestones, and implemented comprehensive testing strategies. The project was delivered on schedule with no major incidents.',
  }),
  technical: (req) => ({
    question: `Describe your experience with ${req.requiredSkills.slice(0, 3).join(', ')}.`,
    generate: () => `I have extensive hands-on experience with ${req.requiredSkills.slice(0, 3).join(', ')}, having applied these technologies across multiple production systems. My expertise includes designing scalable architectures, implementing best practices, and mentoring team members in these technologies.`,
  }),
  teamwork: () => ({
    question: 'How do you work in a team?',
    generate: () => 'I thrive in collaborative environments and believe the best results come from diverse perspectives. I communicate openly, share knowledge freely, and actively support my teammates. I am comfortable both leading initiatives and contributing as a reliable team member.',
  }),
  achievements: () => ({
    question: 'What is your most significant professional achievement?',
    generate: () => 'My most significant achievement was leading the redesign of a critical system that improved performance by 60% and reduced operational costs by 40%. This required coordinating across engineering, product, and operations teams while maintaining existing service levels during the transition.',
  }),
}

export function generateAnswers(
  request: GenerationRequest,
  topics: QuestionnaireTopic[]
): QuestionnaireAnswer[] {
  return topics.map(topic => {
    const template = QUESTIONNAIRE_TEMPLATES[topic](request)
    const answer = template.generate()
    return {
      topic,
      question: template.question,
      answer,
      wordCount: answer.split(/\s+/).length,
      confidence: calculateConfidence(topic, request),
    }
  })
}

export function generateAllDefaultAnswers(request: GenerationRequest): QuestionnaireAnswer[] {
  const topics: QuestionnaireTopic[] = [
    'about_yourself', 'why_company', 'why_role', 'expected_salary',
    'notice_period', 'work_authorization', 'availability', 'strengths',
    'weaknesses', 'career_goals',
  ]
  return generateAnswers(request, topics)
}

function generateAboutYourself(req: GenerationRequest): string {
  const skills = req.requiredSkills.slice(0, 4).join(', ')
  return `I am a ${req.experienceLevel || 'experienced'} professional with a strong background in ${req.companyIndustry || 'software development'}. My core expertise includes ${skills}, and I have a proven track record of delivering high-impact solutions. I am passionate about leveraging technology to solve real-world problems and continuously expanding my skills.`
}

function generateWhyCompany(req: GenerationRequest): string {
  let answer = `I am drawn to ${req.companyName} because of its reputation for innovation and excellence in the ${req.companyIndustry || 'technology'} industry.`
  if (req.companyDescription) {
    const desc = req.companyDescription.split('.').slice(0, 2).join('.')
    answer += ` ${desc}`
  }
  answer += ` I believe my skills and values align well with the company's mission, and I am excited about the opportunity to contribute to meaningful projects.`
  return answer
}

function generateWhyRole(req: GenerationRequest): string {
  const skills = req.requiredSkills.slice(0, 3).join(', ')
  return `The ${req.jobTitle} role at ${req.companyName} is an ideal fit for my skills in ${skills}. I am excited about the opportunity to apply my experience to the challenges described in the role, particularly in areas where I have deep expertise. This position aligns perfectly with my career trajectory and professional interests.`
}

function generateSalary(req: GenerationRequest): string {
  if (req.salaryRange) {
    return `Based on my experience and the market rate for this role, my expected salary range is ${req.salaryRange.currency || '$'}${req.salaryRange.min.toLocaleString()} to ${req.salaryRange.currency || '$'}${req.salaryRange.max.toLocaleString()}. I am open to discussing this based on the total compensation package.`
  }
  return 'I am open to discussing compensation based on the full package and responsibilities. Market rate for my experience level would be appropriate.'
}

function generateStrengths(): string {
  return 'My greatest strengths are my technical problem-solving ability, strong communication skills, and adaptability. I excel at breaking down complex problems into manageable solutions and communicating technical concepts to non-technical stakeholders. I am also highly adaptable and thrive in fast-paced environments.'
}

function generateWeaknesses(): string {
  return 'I sometimes focus too much on details, which can slow down initial progress. I have been actively working on this by setting time limits for perfectionism and focusing on iterative delivery. I also make a conscious effort to delegate and trust my teammates, which has been a valuable growth area.'
}

function calculateConfidence(topic: QuestionnaireTopic, request: GenerationRequest): number {
  if (topic === 'why_company' && request.companyDescription) return 90
  if (topic === 'why_role' && request.jobDescription) return 90
  if (topic === 'expected_salary' && request.salaryRange) return 85
  if (topic === 'about_yourself' && request.requiredSkills.length > 0) return 85
  if (topic === 'technical' && request.requiredSkills.length > 0) return 80
  return 70
}
