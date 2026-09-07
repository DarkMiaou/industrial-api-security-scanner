// ===========================
// TestResultCard.tsx
// ©AngelaMos | 2025
// ===========================

import { TEST_TYPE_LABELS } from '@/config/constants'
import { statusLabel } from '@/lib/scanPresentation'
import { useUIStore } from '@/store/uiStore'
import type { TestResult } from '@/types/scan.types'
import './TestResultCard.css'

interface TestResultCardProps {
  result: TestResult
  position: number
}

export const TestResultCard = ({
  result,
  position,
}: TestResultCardProps): React.ReactElement => {
  const showEvidence = useUIStore(
    (state) => state.testResults.expandedTests[result.id] ?? false
  )
  const toggleTestExpanded = useUIStore((state) => state.toggleTestExpanded)

  return (
    <article
      className={`test-result-card test-result-card--${result.status}`}
      aria-labelledby={`result-${result.id.toString()}-title`}
    >
      <div className="test-result-card__header">
        <span className="test-result-card__position">
          {position.toString().padStart(2, '0')}
        </span>
        <div className="test-result-card__title-section">
          <span className="test-result-card__control">
            {TEST_TYPE_LABELS[result.test_name]}
          </span>
          <h3
            id={`result-${result.id.toString()}-title`}
            className="test-result-card__title"
          >
            {result.title}
          </h3>
          <div className="test-result-card__route">
            <span>{result.method}</span>
            <code>{result.endpoint}</code>
          </div>
        </div>
        <div className="test-result-card__badges">
          <span
            className={`test-result-card__badge test-result-card__badge--${result.status}`}
          >
            {statusLabel(result.status)}
          </span>
          <span
            className={`test-result-card__severity test-result-card__severity--${result.severity}`}
          >
            {result.severity}
          </span>
        </div>
      </div>

      <div className="test-result-card__content">
        <div className="test-result-card__summary-grid">
          <section className="test-result-card__section">
            <h4 className="test-result-card__section-title">Observation</h4>
            <p className="test-result-card__details">{result.details}</p>
          </section>
          <section className="test-result-card__impact">
            <h4 className="test-result-card__section-title">OT impact</h4>
            <p className="test-result-card__details">{result.ot_impact}</p>
          </section>
        </div>

        {result.recommendations_json.length > 0 ? (
          <section className="test-result-card__section">
            <h4 className="test-result-card__section-title">
              Recommended action
            </h4>
            <ul className="test-result-card__recommendations">
              {result.recommendations_json.map((recommendation) => (
                <li
                  key={`${result.id.toString()}-rec-${recommendation}`}
                  className="test-result-card__recommendation"
                >
                  {recommendation}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {Object.keys(result.evidence_json).length > 0 ? (
          <section className="test-result-card__section test-result-card__technical">
            <button
              type="button"
              onClick={() => toggleTestExpanded(result.id)}
              className="test-result-card__evidence-toggle"
              aria-expanded={showEvidence}
            >
              <span aria-hidden="true">{showEvidence ? '−' : '+'}</span>
              Technical evidence
              <small>Redacted diagnostic data</small>
            </button>
            {showEvidence ? (
              <pre className="test-result-card__evidence">
                {JSON.stringify(result.evidence_json, null, 2)}
              </pre>
            ) : null}
          </section>
        ) : null}
      </div>
    </article>
  )
}
