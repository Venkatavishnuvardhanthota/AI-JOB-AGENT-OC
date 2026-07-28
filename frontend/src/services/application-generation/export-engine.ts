import type { ExportResult, ExportFormat, ApplicationPackage } from './types'

const PREFIX = 'ajapp_gen_exp_'

function get<T>(key: string, fallback: T): T {
  try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback } catch { return fallback }
}
function set<T>(key: string, value: T): void {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
}

export function exportPackage(pkg: ApplicationPackage, format: ExportFormat): ExportResult {
  const result: ExportResult = {
    packageId: pkg.id,
    format,
    url: `/exports/${pkg.id}/${format}`,
    filename: `${pkg.companyName.replace(/\s+/g, '_')}_${pkg.jobTitle.replace(/\s+/g, '_')}_application.${getExtension(format)}`,
    size: estimateSize(pkg, format),
    createdAt: new Date().toISOString(),
  }
  const exports = get<ExportResult[]>(`${PREFIX}${pkg.id}`, [])
  exports.unshift(result)
  set(`${PREFIX}${pkg.id}`, exports.slice(0, 50))
  return result
}

export function exportAllFormats(pkg: ApplicationPackage): ExportResult[] {
  const formats: ExportFormat[] = ['pdf', 'docx', 'markdown', 'json']
  return formats.map(f => exportPackage(pkg, f))
}

export function getExports(packageId: string): ExportResult[] {
  return get<ExportResult[]>(`${PREFIX}${packageId}`, [])
}

export function generateMarkdown(pkg: ApplicationPackage): string {
  const lines: string[] = []
  lines.push(`# Application Package: ${pkg.jobTitle} at ${pkg.companyName}`)
  lines.push('')
  lines.push('## Generated Resume')
  lines.push(pkg.resume.summary)
  lines.push('')
  for (const section of pkg.resume.sections) {
    if (!section.included) continue
    lines.push(`### ${section.title}`)
    for (const item of section.items) {
      lines.push(`- **${item.title}**${item.subtitle ? ` - ${item.subtitle}` : ''}`)
      for (const bullet of item.bullets) {
        lines.push(`  - ${bullet}`)
      }
    }
    lines.push('')
  }
  if (pkg.coverLetter) {
    lines.push('## Cover Letter')
    lines.push(pkg.coverLetter.body)
    lines.push('')
  }
  if (pkg.questionnaire.length > 0) {
    lines.push('## Questionnaire Answers')
    for (const q of pkg.questionnaire) {
      lines.push(`### ${q.question}`)
      lines.push(q.answer)
      lines.push('')
    }
  }
  return lines.join('\n')
}

export function generateJSON(pkg: ApplicationPackage): string {
  return JSON.stringify({
    jobTitle: pkg.jobTitle,
    companyName: pkg.companyName,
    resume: {
      summary: pkg.resume.summary,
      sections: pkg.resume.sections.filter(s => s.included).map(s => ({
        title: s.title, items: s.items.map(i => ({ title: i.title, subtitle: i.subtitle, bullets: i.bullets })),
      })),
      skills: pkg.resume.skills.filter(s => s.highlighted).map(s => s.name),
      atsScore: pkg.resume.metadata.atsScore,
    },
    coverLetter: pkg.coverLetter ? { body: pkg.coverLetter.body, subject: pkg.coverLetter.subject } : null,
    questionnaire: pkg.questionnaire.map(q => ({ question: q.question, answer: q.answer })),
    confidenceScore: pkg.metadata.confidenceScore,
    generatedAt: pkg.createdAt,
  }, null, 2)
}

function getExtension(format: ExportFormat): string {
  const extMap: Record<ExportFormat, string> = { pdf: 'pdf', docx: 'docx', markdown: 'md', json: 'json', bundle: 'zip' }
  return extMap[format]
}

function estimateSize(pkg: ApplicationPackage, format: ExportFormat): number {
  const baseSize = pkg.resume.summary.length + (pkg.coverLetter?.body.length ?? 0) + pkg.questionnaire.reduce((s, q) => s + q.answer.length, 0)
  if (format === 'json') return baseSize
  if (format === 'markdown') return Math.round(baseSize * 1.1)
  if (format === 'pdf') return Math.round(baseSize * 1.5)
  if (format === 'docx') return Math.round(baseSize * 1.3)
  return Math.round(baseSize * 2)
}
