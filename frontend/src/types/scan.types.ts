// ===========================
// scan.types.ts
// ©AngelaMos | 2025
// ===========================

import type {
  GatewayProfile,
  ScanExecutionStatus,
  ScanStatus,
  ScanTestType,
  Severity,
} from '@/config/constants'

export type {
  GatewayProfile,
  ScanExecutionStatus,
  ScanTestType,
  ScanStatus,
  Severity,
}

export interface TestResult {
  id: number
  scan_id: number
  test_name: ScanTestType
  status: ScanStatus
  severity: Severity
  title: string
  method: string
  endpoint: string
  details: string
  ot_impact: string
  evidence_json: Record<string, unknown>
  recommendations_json: string[]
  created_at: string
}

export interface Scan {
  id: number
  user_id: number
  target_url: string
  target_key: 'ot-gateway-demo'
  target_name: string
  profile: GatewayProfile
  status: ScanExecutionStatus
  authorization_confirmed: boolean
  score: number | null
  request_count: number
  duration_ms: number | null
  scan_date: string
  completed_at: string | null
  created_at: string
  test_results: TestResult[]
}

export interface CreateScanRequest {
  target: 'ot-gateway-demo'
  tests_to_run: ScanTestType[]
  authorization_confirmed: true
}

export type CreateScanResponse = Scan

export type GetScansResponse = Scan[]

export type GetScanResponse = Scan
