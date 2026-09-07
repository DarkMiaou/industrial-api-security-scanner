// ===========================
// ScansList.tsx
// ©AngelaMos | 2025
// ===========================

import { Link } from 'react-router-dom'
import {
  GATEWAY_PROFILE_LABELS,
  SCAN_EXECUTION_STATUS_LABELS,
} from '@/config/constants'
import { useGetScans } from '@/hooks/useScan'
import { countResults, scoreBand } from '@/lib/scanPresentation'
import { formatDuration, formatRelativeTime } from '@/lib/utils'
import './ScansList.css'

export const ScansList = (): React.ReactElement => {
  const { data: scans, isLoading, error } = useGetScans()

  if (isLoading) {
    return (
      <div className="scans-list__loading">
        <p>Loading scans...</p>
      </div>
    )
  }

  if (error !== null && error !== undefined) {
    return (
      <div className="scans-list__error">
        <p>Failed to load scans. Please try again.</p>
      </div>
    )
  }

  if (
    scans === null ||
    scans === undefined ||
    !Array.isArray(scans) ||
    scans.length === 0
  ) {
    return (
      <div className="scans-list__empty">
        <span className="scans-list__empty-icon" aria-hidden="true">
          00
        </span>
        <h3 className="scans-list__empty-title">No assessments yet</h3>
        <p className="scans-list__empty-text">
          Configure the seven bounded controls above to create the first OT
          security baseline.
        </p>
      </div>
    )
  }

  return (
    <div className="scans-list">
      <div className="scans-list__table">
        <div className="scans-list__header">
          <div className="scans-list__header-cell">Assessment</div>
          <div className="scans-list__header-cell">Profile</div>
          <div className="scans-list__header-cell">Result</div>
          <div className="scans-list__header-cell">Activity</div>
          <div className="scans-list__header-cell">Actions</div>
        </div>

        <div className="scans-list__body">
          {scans.map((scan) => {
            const counts = countResults(scan)

            return (
              <div key={scan.id} className="scans-list__row">
                <div className="scans-list__cell" data-label="Assessment">
                  <div className="scans-list__identity">
                    <strong>{scan.target_name}</strong>
                    <span>
                      #{scan.id.toString()} · {formatRelativeTime(scan.scan_date)}
                    </span>
                  </div>
                </div>
                <div className="scans-list__cell" data-label="Profile">
                  <span
                    className={`scans-list__profile scans-list__profile--${scan.profile}`}
                  >
                    {GATEWAY_PROFILE_LABELS[scan.profile]}
                  </span>
                </div>
                <div className="scans-list__cell" data-label="Result">
                  <div className="scans-list__outcome">
                    <span
                      className={`scans-list__score scans-list__score--${scoreBand(
                        scan.score
                      )}`}
                    >
                      {scan.score === null ? '—' : scan.score.toString()}
                    </span>
                    <span className="scans-list__counts">
                      {counts.vulnerable.toString()} findings ·{' '}
                      {counts.error.toString()} errors
                    </span>
                  </div>
                </div>
                <div className="scans-list__cell" data-label="Activity">
                  <div className="scans-list__activity">
                    <span
                      className={`scans-list__execution scans-list__execution--${scan.status}`}
                    >
                      {SCAN_EXECUTION_STATUS_LABELS[scan.status]}
                    </span>
                    <small>
                      {scan.request_count.toString()} req ·{' '}
                      {formatDuration(scan.duration_ms)}
                    </small>
                  </div>
                </div>
                <div className="scans-list__cell" data-label="Actions">
                  <Link
                    to={`/scans/${scan.id.toString()}`}
                    className="scans-list__view-link"
                  >
                    Open results →
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
