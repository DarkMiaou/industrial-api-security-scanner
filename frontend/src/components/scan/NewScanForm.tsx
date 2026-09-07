// ===========================
// NewScanForm.tsx
// ©AngelaMos | 2025
// ===========================

import { useEffect, useState } from 'react'
import { Button } from '@/components/common/Button'
import { LoadingOverlay } from '@/components/common/LoadingOverlay'
import {
  OT_GATEWAY_TARGET,
  SCAN_TEST_GROUPS,
  SCAN_TEST_ORDER,
  type ScanTestType,
  TEST_TYPE_LABELS,
} from '@/config/constants'
import { useCreateScan } from '@/hooks/useScan'
import { scanSchema } from '@/lib/validation'
import { useUIStore } from '@/store/uiStore'
import './ScanForm.css'

export const NewScanForm = (): React.ReactElement => {
  const scanFormState = useUIStore((state) => state.scanForm)
  const setScanFormField = useUIStore((state) => state.setScanFormField)
  const clearScanForm = useUIStore((state) => state.clearScanForm)
  const clearExpiredData = useUIStore((state) => state.clearExpiredData)

  const selectedTests = scanFormState.selectedTests
  const authorizationConfirmed = scanFormState.authorizationConfirmed
  const [errors, setErrors] = useState<{
    testsToRun?: string
    authorizationConfirmed?: string
  }>({})

  const { mutate: createScan, isPending } = useCreateScan()

  useEffect(() => {
    clearExpiredData()
    const currentForm = useUIStore.getState().scanForm

    if (currentForm.expiresAt === null) {
      setScanFormField('selectedTests', [...SCAN_TEST_ORDER])
    }
  }, [clearExpiredData, setScanFormField])

  const validateForm = (): boolean => {
    const result = scanSchema.safeParse({
      target: OT_GATEWAY_TARGET.KEY,
      testsToRun: selectedTests,
      authorizationConfirmed,
    })

    if (!result.success) {
      const newErrors: {
        testsToRun?: string
        authorizationConfirmed?: string
      } = {}

      result.error.issues.forEach((err) => {
        const field = err.path[0] as keyof typeof newErrors
        if (field !== null && field !== undefined) {
          newErrors[field] = err.message
        }
      })

      setErrors(newErrors)
      return false
    }

    setErrors({})
    return true
  }

  const handleTestToggle = (test: ScanTestType): void => {
    const newTests = selectedTests.includes(test)
      ? selectedTests.filter((t) => t !== test)
      : [...selectedTests, test]

    setScanFormField('selectedTests', newTests)
    setErrors({})
  }

  const handleGroupToggle = (tests: readonly ScanTestType[]): void => {
    const groupSelected = tests.every((test) => selectedTests.includes(test))
    const newTests = groupSelected
      ? selectedTests.filter((test) => !tests.includes(test))
      : Array.from(new Set([...selectedTests, ...tests]))

    setScanFormField('selectedTests', newTests)
    setErrors({})
  }

  const handleSelectAll = (): void => {
    const allSelected = selectedTests.length === SCAN_TEST_ORDER.length
    const newTests = allSelected ? [] : [...SCAN_TEST_ORDER]
    setScanFormField('selectedTests', newTests)
    setErrors({})
  }

  const handleAuthorizationChange = (confirmed: boolean): void => {
    setScanFormField('authorizationConfirmed', confirmed)
    setErrors({})
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    createScan(
      {
        target: OT_GATEWAY_TARGET.KEY,
        tests_to_run: selectedTests,
        authorization_confirmed: true,
      },
      {
        onSuccess: () => {
          clearScanForm()
        },
      }
    )
  }

  return (
    <>
      {isPending ? <LoadingOverlay tests={selectedTests} /> : null}
      <form className="scan-form" onSubmit={handleSubmit}>
        <section className="scan-form__target" aria-label="Fixed OT scan target">
          <div className="scan-form__target-icon" aria-hidden="true">
            WP
          </div>
          <div className="scan-form__target-copy">
            <span className="scan-form__eyebrow">Authorized local target</span>
            <strong>{OT_GATEWAY_TARGET.DISPLAY_NAME}</strong>
            <span>{OT_GATEWAY_TARGET.KEY}</span>
          </div>
          <div className="scan-form__target-facts">
            <span>
              <b>Scope</b> Local Docker network
            </span>
            <span>
              <b>Profile</b> Detected at runtime
            </span>
          </div>
          <span className="scan-form__locked">Locked target</span>
        </section>

        <div className="scan-form__controls-heading">
          <div>
            <span className="scan-form__eyebrow">Control plan</span>
            <h3>Choose the checks to execute</h3>
          </div>
          <button
            type="button"
            className="scan-form__select-all"
            onClick={handleSelectAll}
          >
            {selectedTests.length === SCAN_TEST_ORDER.length
              ? 'Clear selection'
              : 'Select all 7'}
          </button>
        </div>

        {errors.testsToRun !== null && errors.testsToRun !== undefined ? (
          <span className="scan-form__error" role="alert">
            {errors.testsToRun}
          </span>
        ) : null}

        <div className="scan-form__groups">
          {SCAN_TEST_GROUPS.map((group) => {
            const selectedCount = group.tests.filter((test) =>
              selectedTests.includes(test)
            ).length
            const groupSelected = selectedCount === group.tests.length

            return (
              <fieldset key={group.id} className="scan-form__group">
                <legend className="scan-form__group-heading">
                  <span>
                    <strong>{group.title}</strong>
                    <small>{group.description}</small>
                  </span>
                  <button
                    type="button"
                    className="scan-form__group-toggle"
                    onClick={() => handleGroupToggle(group.tests)}
                  >
                    {groupSelected ? 'Deselect group' : 'Select group'}
                  </button>
                </legend>
                <div className="scan-form__checkboxes">
                  {group.tests.map((test) => (
                    <label
                      key={test}
                      className={`scan-form__checkbox-label ${
                        selectedTests.includes(test)
                          ? 'scan-form__checkbox-label--selected'
                          : ''
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedTests.includes(test)}
                        onChange={() => handleTestToggle(test)}
                        className="scan-form__checkbox"
                      />
                      <span>{TEST_TYPE_LABELS[test]}</span>
                    </label>
                  ))}
                </div>
                <span className="scan-form__group-count">
                  {selectedCount.toString()} of {group.tests.length.toString()}{' '}
                  selected
                </span>
              </fieldset>
            )
          })}
        </div>

        <div className="scan-form__footer">
          <div className="scan-form__authorization-wrap">
            <label className="scan-form__authorization">
              <input
                type="checkbox"
                checked={authorizationConfirmed}
                onChange={(event) =>
                  handleAuthorizationChange(event.target.checked)
                }
                className="scan-form__checkbox"
              />
              <span>
                <strong>I am authorized to run this assessment.</strong>
                <small>
                  The scan is limited to the local OT laboratory and never targets
                  an arbitrary address.
                </small>
              </span>
            </label>
            {errors.authorizationConfirmed !== undefined ? (
              <span className="scan-form__error" role="alert">
                {errors.authorizationConfirmed}
              </span>
            ) : null}
          </div>

          <div className="scan-form__submit">
            <span>{selectedTests.length.toString()} controls selected</span>
            <Button type="submit" isLoading={isPending} disabled={isPending}>
              {isPending ? 'Running assessment...' : 'Run OT assessment'}
            </Button>
          </div>
        </div>
      </form>
    </>
  )
}
