import { SCAN_TEST_ORDER, type ScanStatus } from '@/config/constants'
import type { Scan, TestResult } from '@/types/scan.types'

export interface ResultCounts {
  safe: number
  vulnerable: number
  error: number
}

export const sortTestResults = (results: TestResult[]): TestResult[] => {
  return [...results].sort(
    (left, right) =>
      SCAN_TEST_ORDER.indexOf(left.test_name) -
      SCAN_TEST_ORDER.indexOf(right.test_name)
  )
}

export const countResults = (scan: Scan): ResultCounts => {
  return scan.test_results.reduce<ResultCounts>(
    (counts, result) => {
      counts[result.status] += 1
      return counts
    },
    { safe: 0, vulnerable: 0, error: 0 }
  )
}

export const scoreBand = (
  score: number | null
): 'strong' | 'attention' | 'critical' | 'unknown' => {
  if (score === null) return 'unknown'
  if (score >= 80) return 'strong'
  if (score >= 50) return 'attention'
  return 'critical'
}

export const statusLabel = (status: ScanStatus): string => {
  if (status === 'safe') return 'Safe'
  if (status === 'vulnerable') return 'Vulnerable'
  return 'Error'
}
