/**
 * ©AngelaMos | 2025
 * All hardcoded values, API endpoints, and configuration constants
 */

/**
 * API Configuration
 */
export const API_BASE_URL =
  import.meta.env.VITE_API_URL !== undefined &&
  import.meta.env.VITE_API_URL !== null &&
  import.meta.env.VITE_API_URL !== ''
    ? import.meta.env.VITE_API_URL
    : '/api'

/**
 * Auth API Endpoints
 */
export const AUTH_ENDPOINTS = {
  REGISTER: '/auth/register',
  LOGIN: '/auth/login',
} as const

export type AuthEndpoint = (typeof AUTH_ENDPOINTS)[keyof typeof AUTH_ENDPOINTS]

/**
 * Auth Error Messages
 */
export const AUTH_ERROR_MESSAGES = {
  INVALID_LOGIN_RESPONSE: 'Invalid login response from server',
  INVALID_REGISTER_RESPONSE: 'Invalid register response from server',
  LOGIN_FAILED: 'Failed to login',
  REGISTER_FAILED: 'Failed to register',
  LOGOUT_FAILED: 'Failed to logout',
} as const

export type AuthErrorMessage =
  (typeof AUTH_ERROR_MESSAGES)[keyof typeof AUTH_ERROR_MESSAGES]

export const AUTH_ERROR_CONTEXTS = {
  LOGIN: 'auth.login',
  REGISTER: 'auth.register',
  LOGOUT: 'auth.logout',
} as const

export type AuthErrorContext =
  (typeof AUTH_ERROR_CONTEXTS)[keyof typeof AUTH_ERROR_CONTEXTS]

/**
 * LocalStorage Keys
 */
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  USER: 'user',
} as const

/**
 * Application Constants
 */
export const APP_NAME = 'IASS-OT'
export const APP_VERSION = '1.0.1'

export const OT_GATEWAY_TARGET = {
  KEY: 'ot-gateway-demo',
  DISPLAY_NAME: 'Water Pump Gateway',
} as const

export const GATEWAY_PROFILES = {
  VULNERABLE: 'vulnerable',
  HARDENED: 'hardened',
} as const

export type GatewayProfile =
  (typeof GATEWAY_PROFILES)[keyof typeof GATEWAY_PROFILES]

export const SCAN_EXECUTION_STATUS = {
  RUNNING: 'running',
  COMPLETED: 'completed',
  PARTIAL: 'partial',
  FAILED: 'failed',
} as const

export type ScanExecutionStatus =
  (typeof SCAN_EXECUTION_STATUS)[keyof typeof SCAN_EXECUTION_STATUS]

export const SCAN_EXECUTION_STATUS_LABELS: Record<ScanExecutionStatus, string> = {
  [SCAN_EXECUTION_STATUS.RUNNING]: 'Running',
  [SCAN_EXECUTION_STATUS.COMPLETED]: 'Completed',
  [SCAN_EXECUTION_STATUS.PARTIAL]: 'Partial',
  [SCAN_EXECUTION_STATUS.FAILED]: 'Failed',
}

export const GATEWAY_PROFILE_LABELS: Record<GatewayProfile, string> = {
  [GATEWAY_PROFILES.VULNERABLE]: 'Vulnerable profile',
  [GATEWAY_PROFILES.HARDENED]: 'Hardened profile',
}

/**
 * Scan Test Types
 */
export const SCAN_TEST_TYPES = {
  RATE_LIMIT: 'rate_limit',
  AUTH: 'auth',
  SQLI: 'sqli',
  IDOR: 'idor',
  OT_COMMAND_AUTHZ: 'ot_command_authz',
  OT_AUDIT: 'ot_audit',
  OT_RATE_LIMIT: 'ot_rate_limit',
} as const

export type ScanTestType = (typeof SCAN_TEST_TYPES)[keyof typeof SCAN_TEST_TYPES]

export const TEST_TYPE_LABELS: Record<ScanTestType, string> = {
  [SCAN_TEST_TYPES.RATE_LIMIT]: 'Rate Limiting',
  [SCAN_TEST_TYPES.AUTH]: 'Authentication',
  [SCAN_TEST_TYPES.SQLI]: 'SQL Injection',
  [SCAN_TEST_TYPES.IDOR]: 'IDOR/BOLA',
  [SCAN_TEST_TYPES.OT_COMMAND_AUTHZ]: 'OT Command Authorization',
  [SCAN_TEST_TYPES.OT_AUDIT]: 'OT Audit Trail',
  [SCAN_TEST_TYPES.OT_RATE_LIMIT]: 'OT Command Rate Limiting',
}

export const SCAN_TEST_ORDER: readonly ScanTestType[] = [
  SCAN_TEST_TYPES.AUTH,
  SCAN_TEST_TYPES.IDOR,
  SCAN_TEST_TYPES.SQLI,
  SCAN_TEST_TYPES.RATE_LIMIT,
  SCAN_TEST_TYPES.OT_COMMAND_AUTHZ,
  SCAN_TEST_TYPES.OT_AUDIT,
  SCAN_TEST_TYPES.OT_RATE_LIMIT,
]

export const SCAN_TEST_GROUPS: ReadonlyArray<{
  id: string
  title: string
  description: string
  tests: readonly ScanTestType[]
}> = [
  {
    id: 'api-boundary',
    title: 'API boundary controls',
    description:
      'Identity, object access, input validation and login throttling.',
    tests: [
      SCAN_TEST_TYPES.AUTH,
      SCAN_TEST_TYPES.IDOR,
      SCAN_TEST_TYPES.SQLI,
      SCAN_TEST_TYPES.RATE_LIMIT,
    ],
  },
  {
    id: 'ot-safeguards',
    title: 'OT operational safeguards',
    description: 'Command authorization, traceability and command throttling.',
    tests: [
      SCAN_TEST_TYPES.OT_COMMAND_AUTHZ,
      SCAN_TEST_TYPES.OT_AUDIT,
      SCAN_TEST_TYPES.OT_RATE_LIMIT,
    ],
  },
]

/**
 * Test Result Status
 */
export const SCAN_STATUS = {
  VULNERABLE: 'vulnerable',
  SAFE: 'safe',
  ERROR: 'error',
} as const

export type ScanStatus = (typeof SCAN_STATUS)[keyof typeof SCAN_STATUS]

export const STATUS_COLORS: Record<ScanStatus, string> = {
  [SCAN_STATUS.VULNERABLE]: '#dc2626',
  [SCAN_STATUS.SAFE]: '#16a34a',
  [SCAN_STATUS.ERROR]: '#6b7280',
}

/**
 * Severity Levels
 */
export const SEVERITY = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
  INFO: 'info',
} as const

export type Severity = (typeof SEVERITY)[keyof typeof SEVERITY]

export const SEVERITY_COLORS: Record<Severity, string> = {
  [SEVERITY.CRITICAL]: '#dc2626',
  [SEVERITY.HIGH]: '#ea580c',
  [SEVERITY.MEDIUM]: '#f59e0b',
  [SEVERITY.LOW]: '#3b82f6',
  [SEVERITY.INFO]: '#6b7280',
}

/**
 * Scan API Endpoints
 */
export const SCAN_ENDPOINTS = {
  CREATE: '/scans/',
  LIST: '/scans/',
  GET: (id: number) => `/scans/${id.toString()}`,
  DELETE: (id: number) => `/scans/${id.toString()}`,
} as const

/**
 * Scan Error Messages
 */
export const SCAN_ERROR_MESSAGES = {
  INVALID_CREATE_SCAN_RESPONSE: 'Invalid create scan response from server',
  INVALID_GET_SCANS_RESPONSE: 'Invalid get scans response from server',
  INVALID_GET_SCAN_RESPONSE: 'Invalid get scan response from server',
  CREATE_SCAN_FAILED: 'Failed to create scan',
  GET_SCANS_FAILED: 'Failed to fetch scans',
  GET_SCAN_FAILED: 'Failed to fetch scan details',
  DELETE_SCAN_FAILED: 'Failed to delete scan',
} as const

export type ScanErrorMessage =
  (typeof SCAN_ERROR_MESSAGES)[keyof typeof SCAN_ERROR_MESSAGES]

export const SCAN_ERROR_CONTEXTS = {
  CREATE_SCAN: 'scan.createScan',
  GET_SCANS: 'scan.getScans',
  GET_SCAN: 'scan.getScan',
  DELETE_SCAN: 'scan.deleteScan',
} as const

export type ScanErrorContext =
  (typeof SCAN_ERROR_CONTEXTS)[keyof typeof SCAN_ERROR_CONTEXTS]
