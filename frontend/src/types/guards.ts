// ===========================
// guards.ts
// ©AngelaMos | 2025
// ===========================

import {
  GATEWAY_PROFILES,
  SCAN_EXECUTION_STATUS,
  SCAN_STATUS,
  SCAN_TEST_TYPES,
  SEVERITY,
} from '@/config/constants'
import type { LoginResponse, RegisterResponse } from './auth.types'
import type {
  CreateScanResponse,
  GatewayProfile,
  GetScanResponse,
  GetScansResponse,
  Scan,
  ScanExecutionStatus,
  ScanStatus,
  ScanTestType,
  Severity,
  TestResult,
} from './scan.types'

export const isValidLoginResponse = (data: unknown): data is LoginResponse => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  const obj = data as Record<string, unknown>

  return (
    typeof obj.access_token === 'string' &&
    obj.access_token.length > 0 &&
    typeof obj.token_type === 'string'
  )
}

export const isValidRegisterResponse = (
  data: unknown
): data is RegisterResponse => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  const obj = data as Record<string, unknown>

  return (
    typeof obj.id === 'number' &&
    typeof obj.email === 'string' &&
    obj.email.length > 0 &&
    typeof obj.is_active === 'boolean' &&
    typeof obj.created_at === 'string'
  )
}

const isValidScanTestType = (value: unknown): value is ScanTestType => {
  return (
    typeof value === 'string' &&
    Object.values(SCAN_TEST_TYPES).includes(value as ScanTestType)
  )
}

const isValidScanStatus = (value: unknown): value is ScanStatus => {
  return (
    typeof value === 'string' &&
    Object.values(SCAN_STATUS).includes(value as ScanStatus)
  )
}

const isValidSeverity = (value: unknown): value is Severity => {
  return (
    typeof value === 'string' &&
    Object.values(SEVERITY).includes(value as Severity)
  )
}

const isValidGatewayProfile = (value: unknown): value is GatewayProfile => {
  return (
    typeof value === 'string' &&
    Object.values(GATEWAY_PROFILES).includes(value as GatewayProfile)
  )
}

const isValidScanExecutionStatus = (
  value: unknown
): value is ScanExecutionStatus => {
  return (
    typeof value === 'string' &&
    Object.values(SCAN_EXECUTION_STATUS).includes(value as ScanExecutionStatus)
  )
}

const isValidTestResult = (data: unknown): data is TestResult => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  const obj = data as Record<string, unknown>

  return (
    typeof obj.id === 'number' &&
    typeof obj.scan_id === 'number' &&
    isValidScanTestType(obj.test_name) &&
    isValidScanStatus(obj.status) &&
    isValidSeverity(obj.severity) &&
    typeof obj.title === 'string' &&
    typeof obj.method === 'string' &&
    typeof obj.endpoint === 'string' &&
    typeof obj.details === 'string' &&
    typeof obj.ot_impact === 'string' &&
    typeof obj.evidence_json === 'object' &&
    obj.evidence_json !== null &&
    Array.isArray(obj.recommendations_json) &&
    obj.recommendations_json.every((rec: unknown) => typeof rec === 'string') &&
    typeof obj.created_at === 'string'
  )
}

const isValidScan = (data: unknown): data is Scan => {
  if (data === null || data === undefined) return false
  if (typeof data !== 'object') return false

  const obj = data as Record<string, unknown>

  return (
    typeof obj.id === 'number' &&
    typeof obj.user_id === 'number' &&
    typeof obj.target_url === 'string' &&
    obj.target_key === 'ot-gateway-demo' &&
    typeof obj.target_name === 'string' &&
    isValidGatewayProfile(obj.profile) &&
    isValidScanExecutionStatus(obj.status) &&
    typeof obj.authorization_confirmed === 'boolean' &&
    (typeof obj.score === 'number' || obj.score === null) &&
    typeof obj.request_count === 'number' &&
    (typeof obj.duration_ms === 'number' || obj.duration_ms === null) &&
    typeof obj.scan_date === 'string' &&
    (typeof obj.completed_at === 'string' || obj.completed_at === null) &&
    typeof obj.created_at === 'string' &&
    Array.isArray(obj.test_results) &&
    obj.test_results.every((result: unknown) => isValidTestResult(result))
  )
}

export const isValidCreateScanResponse = (
  data: unknown
): data is CreateScanResponse => {
  return isValidScan(data)
}

export const isValidGetScansResponse = (
  data: unknown
): data is GetScansResponse => {
  if (data === null || data === undefined) return false
  if (!Array.isArray(data)) return false

  return data.every((scan: unknown) => isValidScan(scan))
}

export const isValidGetScanResponse = (
  data: unknown
): data is GetScanResponse => {
  return isValidScan(data)
}
