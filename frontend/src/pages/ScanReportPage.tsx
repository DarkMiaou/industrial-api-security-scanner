import { Link, useParams } from 'react-router-dom'
import {
  GATEWAY_PROFILE_LABELS,
  SCAN_EXECUTION_STATUS_LABELS,
  TEST_TYPE_LABELS,
} from '@/config/constants'
import { useGetScan } from '@/hooks/useScan'
import {
  countResults,
  scoreBand,
  sortTestResults,
  statusLabel,
} from '@/lib/scanPresentation'
import { formatDateTime, formatDuration } from '@/lib/utils'
import './ScanReportPage.css'

export const ScanReportPage = (): React.ReactElement => {
  const { id } = useParams<{ id: string }>()
  const scanId = id !== null && id !== undefined ? parseInt(id, 10) : 0
  const { data: scan, isLoading, error } = useGetScan(scanId)

  if (isLoading) {
    return <div className="scan-report__state">Preparing report…</div>
  }

  if (
    (error !== null && error !== undefined) ||
    scan === null ||
    scan === undefined
  ) {
    return (
      <div className="scan-report__state">
        <p>The assessment report could not be loaded.</p>
        <Link to="/">Return to dashboard</Link>
      </div>
    )
  }

  const counts = countResults(scan)
  const results = sortTestResults(scan.test_results)

  return (
    <main className="scan-report">
      <nav className="scan-report__toolbar" aria-label="Report actions">
        <Link to={`/scans/${scan.id.toString()}`}>← Assessment results</Link>
        <button type="button" onClick={() => window.print()}>
          Print or save as PDF
        </button>
      </nav>

      <article className="scan-report__paper">
        <header className="scan-report__header">
          <div>
            <span className="scan-report__kicker">IASS-OT assessment report</span>
            <h1>Industrial API security posture</h1>
            <p>{scan.target_name}</p>
          </div>
          <div className="scan-report__identity">
            <span>Report reference</span>
            <strong>IASS-OT-{scan.id.toString().padStart(4, '0')}</strong>
            <small>{formatDateTime(scan.scan_date)}</small>
          </div>
        </header>

        <section className="scan-report__executive">
          <div
            className={`scan-report__score scan-report__score--${scoreBand(scan.score)}`}
          >
            <span>Security score</span>
            <strong>{scan.score === null ? '—' : scan.score.toString()}</strong>
            <small>/100</small>
          </div>
          <div className="scan-report__summary">
            <span className="scan-report__kicker">Executive summary</span>
            <h2>
              {counts.vulnerable === 0
                ? 'No vulnerable controls were observed.'
                : `${counts.vulnerable.toString()} control findings require attention.`}
            </h2>
            <p>
              The assessment ran {scan.test_results.length.toString()} bounded
              controls against the server-approved local OT gateway. Technical
              evidence and credentials are intentionally excluded from this
              report.
            </p>
          </div>
        </section>

        <section className="scan-report__facts" aria-label="Assessment facts">
          <dl>
            <div>
              <dt>Target</dt>
              <dd>{scan.target_key}</dd>
            </div>
            <div>
              <dt>Gateway profile</dt>
              <dd>{GATEWAY_PROFILE_LABELS[scan.profile]}</dd>
            </div>
            <div>
              <dt>Execution</dt>
              <dd>{SCAN_EXECUTION_STATUS_LABELS[scan.status]}</dd>
            </div>
            <div>
              <dt>Completed</dt>
              <dd>
                {scan.completed_at === null
                  ? 'Not completed'
                  : formatDateTime(scan.completed_at)}
              </dd>
            </div>
            <div>
              <dt>Requests</dt>
              <dd>{scan.request_count.toString()} of 60 maximum</dd>
            </div>
            <div>
              <dt>Duration</dt>
              <dd>{formatDuration(scan.duration_ms)}</dd>
            </div>
          </dl>
        </section>

        <section className="scan-report__distribution">
          <div>
            <strong>{counts.safe.toString()}</strong>
            <span>Safe</span>
          </div>
          <div>
            <strong>{counts.vulnerable.toString()}</strong>
            <span>Vulnerable</span>
          </div>
          <div>
            <strong>{counts.error.toString()}</strong>
            <span>Errors</span>
          </div>
        </section>

        <section className="scan-report__controls">
          <div className="scan-report__section-heading">
            <span className="scan-report__kicker">Control results</span>
            <h2>Findings and recommended actions</h2>
          </div>

          {results.map((result, index) => (
            <article
              key={result.id}
              className={`scan-report__control scan-report__control--${result.status}`}
            >
              <header>
                <span>{(index + 1).toString().padStart(2, '0')}</span>
                <div>
                  <small>{TEST_TYPE_LABELS[result.test_name]}</small>
                  <h3>{result.title}</h3>
                  <code>
                    {result.method} {result.endpoint}
                  </code>
                </div>
                <div className="scan-report__control-status">
                  <strong>{statusLabel(result.status)}</strong>
                  <span>{result.severity}</span>
                </div>
              </header>
              <div className="scan-report__control-body">
                <div>
                  <h4>Observation</h4>
                  <p>{result.details}</p>
                </div>
                <div>
                  <h4>OT impact</h4>
                  <p>{result.ot_impact}</p>
                </div>
              </div>
              {result.recommendations_json.length > 0 ? (
                <div className="scan-report__recommendations">
                  <h4>Recommended action</h4>
                  <ul>
                    {result.recommendations_json.map((recommendation) => (
                      <li key={`${result.id.toString()}-${recommendation}`}>
                        {recommendation}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </article>
          ))}
        </section>

        <footer className="scan-report__footer">
          <p>
            This report describes a controlled educational assessment of a local
            simulated OT gateway. It is not a certification of production
            security.
          </p>
          <span>IASS-OT · Sanitized report</span>
        </footer>
      </article>
    </main>
  )
}
