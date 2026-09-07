// ===========================
// DashboardPage.tsx
// ©AngelaMos | 2025
// ===========================

import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/common/Button'
import { NewScanForm } from '@/components/scan/NewScanForm'
import { ScansList } from '@/components/scan/ScansList'
import { useAuthStore } from '@/store/authStore'
import './DashboardPage.css'

export const DashboardPage = (): React.ReactElement => {
  const navigate = useNavigate()
  const clearAuth = useAuthStore((state) => state.clearAuth)
  const user = useAuthStore((state) => state.user)

  const handleLogout = (): void => {
    clearAuth()
    void navigate('/login')
  }

  return (
    <div className="dashboard">
      <div className="dashboard__container">
        <header className="dashboard__header">
          <div className="dashboard__header-content">
            <div className="dashboard__brand">
              <span className="dashboard__brand-mark" aria-hidden="true">
                OT
              </span>
              <div className="dashboard__header-text">
                <span className="dashboard__eyebrow">
                  Industrial assessment workspace
                </span>
                <h1 className="dashboard__title">IASS-OT</h1>
                <p className="dashboard__subtitle">
                  Bounded API security checks for a simulated water-pump gateway
                </p>
              </div>
            </div>
            <div className="dashboard__header-actions">
              <div className="dashboard__session">
                <span>Signed in</span>
                <strong>{user?.email}</strong>
              </div>
              <Button onClick={handleLogout} variant="ghost" size="sm">
                Sign out
              </Button>
            </div>
          </div>
        </header>

        <div className="dashboard__content">
          <section
            className="dashboard__overview"
            aria-label="Assessment safeguards"
          >
            <div>
              <span className="dashboard__overview-label">Scope</span>
              <strong>One local OT target</strong>
              <small>Server-enforced destination</small>
            </div>
            <div>
              <span className="dashboard__overview-label">Safety envelope</span>
              <strong>60 requests maximum</strong>
              <small>Bounded and reversible controls</small>
            </div>
            <div>
              <span className="dashboard__overview-label">Coverage</span>
              <strong>7 security controls</strong>
              <small>API boundary + OT safeguards</small>
            </div>
          </section>

          <section className="dashboard__section">
            <div className="dashboard__section-heading">
              <div>
                <span className="dashboard__eyebrow">New assessment</span>
                <h2 className="dashboard__section-title">
                  Configure the control run
                </h2>
              </div>
              <span className="dashboard__step">01 / Assess</span>
            </div>
            <NewScanForm />
          </section>

          <section className="dashboard__section">
            <div className="dashboard__section-heading">
              <div>
                <span className="dashboard__eyebrow">Evidence trail</span>
                <h2 className="dashboard__section-title">Recent assessments</h2>
              </div>
              <span className="dashboard__step">Latest 20</span>
            </div>
            <ScansList />
          </section>
        </div>
      </div>
    </div>
  )
}
