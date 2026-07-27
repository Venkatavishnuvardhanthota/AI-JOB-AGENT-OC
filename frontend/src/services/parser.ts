export interface ParsedResume {
  title?: string
  sections: ParsedSection[]
  raw_text: string
  confidence: number
}

export interface ParsedSection {
  section_type: string
  title?: string
  content: Record<string, unknown>
  confidence: number
}

export interface ParserOptions {
  preserveFormatting?: boolean
}

export interface ParserResult<TParsed = ParsedResume> {
  success: boolean
  data?: TParsed
  error?: string
}

export interface ResumeParser {
  parse(file: File, options?: ParserOptions): Promise<ParserResult>
  supports(file: File): boolean
}
