// ===========================
// ScanResultsPage.tsx
// ©AngelaMos | 2025
// ===========================

import { Link, useParams } from 'react-router-dom'
import { TestResultCard } from '@/components/scan/TestResultCard'
import {
  GATEWAY_PROFILE_LABELS,
  SCAN_EXECUTION_STATUS_LABELS,
} from '@/config/constants'
import { useGetScan } from '@/hooks/useScan'
import { countResults, scoreBand, sortTestResults } from '@/lib/scanPresentation'
import { formatDateTime, formatDuration } from '@/lib/utils'
import './ScanResultsPage.css'

export const ScanResultsPage = (): React.ReactElement => {
  const { id } = useParams<{ id: string }>()
  const scanId = id !== null && id !== undefined ? parseInt(id, 10) : 0
  const { data: scan, isLoading, error } = useGetScan(scanId)

  if (isLoading) {
    return (
      <div className="scan-results__loading">
        <span className="scan-results__loader" aria-hidden="true" />
        <p>Loading assessment results…</p>
      </div>
    )
  }

  if (error !== null && error !== undefined) {
    return (
      <div className="scan-results__error">
        <p>Assessment results could not be loaded.</p>
        <Link to="/" className="scan-results__back-link">
          Return to dashboard
        </Link>
      </div>
    )
  }

  if (scan === null || scan === undefined) {
    return (
      <div className="scan-results__error">
        <p>Assessment not found.</p>
        <Link to="/" className="scan-results__back-link">
          Return to dashboard
        </Link>
      </div>
    )
  }

  const counts = countResults(scan)
  const results = sortTestResults(scan.test_results)

  return (
    <main className="scan-results">
      <div className="scan-results__container">
        <nav className="scan-results__nav" aria-label="Assessment navigation">
          <Link to="/" className="scan-results__back-link">
            ← Dashboard
          </Link>
          <Link
            to={`/scans/${scan.id.toString()}/report`}
            className="scan-results__report-link"
          >
            Open printable report
          </Link>
        </nav>

        <header className="scan-results__hero">
          <div className="scan-results__hero-copy">
            <span className="scan-results__eyebrow">
              Assessment #{scan.id.toString()}
            </span>
            <h1>OT security assessment</h1>
            <p>
              {scan.target_name} · {formatDateTime(scan.scan_date)}
            </p>
            <div className="scan-results__hero-badges">
              <span
                className={`scan-results__profile scan-results__profile--${scan.profile}`}
              >
                {GATEWAY_PROFILE_LABELS[scan.profile]}
              </span>
              <span
                className={`scan-results__execution scan-results__execution--${scan.status}`}
              >
                {SCAN_EXECUTION_STATUS_LABELS[scan.status]}
              </span>
            </div>
          </div>
          <div
            className={`scan-results__score scan-results__score--${scoreBand(scan.score)}`}
          >
            <span>Security score</span>
            <strong>{scan.score === null ? '—' : scan.score.toString()}</strong>
            <small>/ 100</small>
          </div>
        </header>

        <section
          className="scan-results__metrics"
          aria-label="Assessment summary"
        >
          <div>
            <span>Controls</span>
            <strong>{scan.test_results.length.toString()} / 7</strong>
          </div>
          <div>
            <span>Safe</span>
            <strong className="scan-results__metric-safe">
              {counts.safe.toString()}
            </strong>
          </div>
          <div>
            <span>Findings</span>
            <strong className="scan-results__metric-vulnerable">
              {counts.vulnerable.toString()}
            </strong>
          </div>
          <div>
            <span>Errors</span>
            <strong>{counts.error.toString()}</strong>
          </div>
          <div>
            <span>Requests</span>
            <strong>{scan.request_count.toString()} / 60</strong>
          </div>
          <div>
            <span>Duration</span>
            <strong>{formatDuration(scan.duration_ms)}</strong>
          </div>
        </section>

        <section className="scan-results__scope">
          <div>
            <span className="scan-results__eyebrow">Execution scope</span>
            <p>
              The destination was fixed by the backend and authorization was
              explicitly confirmed before execution.
            </p>
          </div>
          <dl>
            <div>
              <dt>Target</dt>
              <dd>{scan.target_key}</dd>
            </div>
            <div>
              <dt>Completed</dt>
              <dd>
                {scan.completed_at === null
                  ? 'Not completed'
                  : formatDateTime(scan.completed_at)}
              </dd>
            </div>
          </dl>
        </section>

        <div className="scan-results__results-heading">
          <div>
            <span className="scan-results__eyebrow">Control evidence</span>
            <h2>Detailed results</h2>
          </div>
          <section
            className="scan-results__legend"
            aria-label="Result status legend"
          >
            <span className="scan-results__legend-safe">Safe</span>
            <span className="scan-results__legend-vulnerable">Vulnerable</span>
            <span className="scan-results__legend-error">Error</span>
          </section>
        </div>

        <div className="scan-results__tests">
          {results.map((result, index) => (
            <TestResultCard
              key={result.id}
              result={result}
              position={index + 1}
            />
          ))}
        </div>
      </div>
    </main>
  )
}
