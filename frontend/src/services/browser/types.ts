export type BrowserProvider = 'chromium' | 'firefox' | 'webkit'
export type BrowserStatus = 'idle' | 'running' | 'error' | 'closed'
export type SessionStatus = 'active' | 'paused' | 'expired' | 'closed'
export type NavigationStatus = 'success' | 'redirect' | 'timeout' | 'error' | 'cancelled'
export type ElementType = 'input' | 'button' | 'link' | 'dropdown' | 'checkbox' | 'radio' | 'textarea' | 'file' | 'select' | 'form' | 'iframe' | 'shadow_dom' | 'unknown'
export type LocatorStrategy = 'css' | 'xpath' | 'text' | 'label' | 'placeholder' | 'role' | 'test_id' | 'data_attr' | 'aria_label'
export type ActionType = 'click' | 'dblclick' | 'hover' | 'type' | 'select' | 'check' | 'uncheck' | 'upload' | 'scroll' | 'focus' | 'blur' | 'drag' | 'drop'
export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

export interface BrowserConfig {
  provider: BrowserProvider
  headless: boolean
  viewport: { width: number; height: number }
  userAgent: string | null
  locale: string | null
  timezoneId: string | null
  geolocation: { latitude: number; longitude: number } | null
  deviceScaleFactor: number
  ignoreHttpsErrors: boolean
  extraArgs: string[]
  proxy: { host: string; port: number; username?: string; password?: string } | null
  downloadPath: string | null
  recordVideo: boolean
  tracesDir: string | null
  screenshotsDir: string | null
}

export const DEFAULT_BROWSER_CONFIG: BrowserConfig = {
  provider: 'chromium',
  headless: true,
  viewport: { width: 1920, height: 1080 },
  userAgent: null,
  locale: null,
  timezoneId: null,
  geolocation: null,
  deviceScaleFactor: 1,
  ignoreHttpsErrors: false,
  extraArgs: [],
  proxy: null,
  downloadPath: null,
  recordVideo: false,
  tracesDir: null,
  screenshotsDir: null,
}

export interface BrowserState {
  id: string
  provider: BrowserProvider
  status: BrowserStatus
  createdAt: string
  lastUsedAt: string | null
  sessions: BrowserSessionSummary[]
  metrics: BrowserMetrics
}

export interface BrowserSessionSummary {
  id: string
  status: SessionStatus
  url: string | null
  tabs: number
  createdAt: string
  lastActivityAt: string
}

export interface BrowserMetrics {
  uptime: number
  pageLoads: number
  actions: number
  errors: number
  memoryUsage: number | null
  cpuUsage: number | null
}

export interface BrowserSession {
  id: string
  browserId: string
  status: SessionStatus
  url: string | null
  tabs: TabInfo[]
  cookies: Record<string, unknown>[]
  storageState: Record<string, unknown> | null
  createdAt: string
  expiresAt: string | null
  lastActivityAt: string
  metadata: Record<string, unknown>
}

export interface TabInfo {
  id: string
  url: string
  title: string
  status: 'loading' | 'ready' | 'error'
  createdAt: string
}

export interface NavigationResult {
  url: string
  finalUrl: string
  status: NavigationStatus
  statusCode: number | null
  duration: number
  redirects: string[]
  error: string | null
  timestamp: string
}

export interface NavigationOptions {
  timeout: number
  waitUntil: 'load' | 'domcontentloaded' | 'networkidle' | 'commit'
  retries: number
  retryDelay: number
  followRedirects: boolean
  referer: string | null
  headers: Record<string, string> | null
}

export const DEFAULT_NAV_OPTIONS: NavigationOptions = {
  timeout: 30000,
  waitUntil: 'networkidle',
  retries: 3,
  retryDelay: 1000,
  followRedirects: true,
  referer: null,
  headers: null,
}

export interface DOMElement {
  tag: string
  type: ElementType
  attributes: Record<string, string>
  text: string | null
  rect: DOMRect | null
  visible: boolean
  enabled: boolean
  readonly: boolean
  checked: boolean | null
  selected: boolean | null
  value: string | null
  name: string | null
  id: string | null
  classes: string[]
  aria: Record<string, string> | null
  children: DOMElement[]
  shadowRoot: boolean
  iframeContent: string | null
}

export interface DOMRect {
  x: number; y: number; width: number; height: number
}

export interface FormDetection {
  formId: string | null
  action: string | null
  method: string | null
  inputs: FormInput[]
  submitButton: { text: string; enabled: boolean } | null
  isUploadForm: boolean
}

export interface FormInput {
  name: string | null
  type: string
  label: string | null
  placeholder: string | null
  required: boolean
  enabled: boolean
  elementType: ElementType
  value: string | null
  options: string[] | null
}

export interface ActionOptions {
  delay: number
  timeout: number
  retries: number
  force: boolean
  noWaitAfter: boolean
  trial: boolean
}

export const DEFAULT_ACTION_OPTIONS: ActionOptions = {
  delay: 50,
  timeout: 10000,
  retries: 2,
  force: false,
  noWaitAfter: false,
  trial: false,
}

export interface HumanBehaviourConfig {
  typingSpeed: { min: number; max: number }
  mouseSpeed: { min: number; max: number }
  pauseBetweenActions: { min: number; max: number }
  scrollSpeed: { min: number; max: number }
  errorRate: number
  randomMistakes: boolean
  enabled: boolean
}

export const DEFAULT_HUMAN_CONFIG: HumanBehaviourConfig = {
  typingSpeed: { min: 50, max: 200 },
  mouseSpeed: { min: 100, max: 500 },
  pauseBetweenActions: { min: 100, max: 500 },
  scrollSpeed: { min: 50, max: 200 },
  errorRate: 0.05,
  randomMistakes: false,
  enabled: true,
}

export interface RetryConfig {
  maxRetries: number
  baseDelay: number
  maxDelay: number
  backoffFactor: number
  retryOnTimeout: boolean
  retryOnNavigation: boolean
  retryOnStaleElement: boolean
}

export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 30000,
  backoffFactor: 2,
  retryOnTimeout: true,
  retryOnNavigation: true,
  retryOnStaleElement: true,
}

export interface LocatorOptions {
  strategy: LocatorStrategy
  selector: string
  timeout: number
  visible: boolean
  enabled: boolean
  exact: boolean
  waitForElement: boolean
  highlight: boolean
}

export const DEFAULT_LOCATOR_OPTIONS: LocatorOptions = {
  strategy: 'css',
  selector: '',
  timeout: 10000,
  visible: true,
  enabled: true,
  exact: false,
  waitForElement: true,
  highlight: false,
}

export interface ScreenshotOptions {
  fullPage: boolean
  type: 'png' | 'jpeg'
  quality: number | null
  selector: string | null
  clip: { x: number; y: number; width: number; height: number } | null
}

export interface ScreenshotResult {
  id: string
  url: string
  filename: string
  path: string
  width: number
  height: number
  type: 'full_page' | 'element' | 'region'
  createdAt: string
  metadata: Record<string, unknown>
}

export interface DownloadResult {
  id: string
  url: string
  filename: string
  path: string
  mimeType: string
  size: number
  createdAt: string
  metadata: Record<string, unknown>
}

export interface LogEntry {
  id: string
  sessionId: string
  level: LogLevel
  source: string
  message: string
  data: Record<string, unknown> | null
  duration: number | null
  timestamp: string
}

export interface UploadResult {
  id: string
  filename: string
  fileSize: number
  mimeType: string
  fieldName: string
  targetUrl: string
  status: 'uploading' | 'uploaded' | 'error'
  createdAt: string
  metadata: Record<string, unknown>
}

export interface BrowserMonitoringReport {
  browserId: string
  sessions: number
  activeSessions: number
  totalNavigations: number
  totalActions: number
  totalErrors: number
  successRate: number
  averageNavigationTime: number
  memoryUsage: number | null
  uptime: number
  recentLogs: LogEntry[]
  warnings: string[]
}
