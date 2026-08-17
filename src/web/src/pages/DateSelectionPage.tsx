import { useMemo, useState } from 'react'
import type { DateRange } from 'react-day-picker'
import type { SchoolSummary } from '../api-client/client'
import { DateRangePicker } from '../components/DateRangePicker'
import { StatusPanel } from '../components/StatusPanel'
import {
  defaultRange,
  localDateToIso,
  validateDateRange,
} from '../lib/dateRange'

interface DateSelectionPageProps {
  school: SchoolSummary
  initialRange?: DateRange
  onChangeSchool: () => void
  onSubmit: (range: { from: string; to: string }) => void
}

export function DateSelectionPage({
  school,
  initialRange,
  onChangeSchool,
  onSubmit,
}: DateSelectionPageProps) {
  const [range, setRange] = useState<DateRange | undefined>(() => {
    if (initialRange) {
      return initialRange
    }
    const bounds = defaultRange()
    return { from: bounds.start, to: bounds.end }
  })

  const validation = useMemo(
    () => validateDateRange(range?.from, range?.to),
    [range],
  )

  function handleSubmit() {
    if (!validation.valid || !range?.from || !range.to) {
      return
    }
    onSubmit({
      from: localDateToIso(range.from),
      to: localDateToIso(range.to),
    })
  }

  return (
    <section className="bento-grid bento-grid--dates">
      <div className="bento-card date-selection-summary">
        <p className="date-selection-summary__eyebrow">선택한 학교</p>
        <h2>{school.schoolName}</h2>
        <div className="flow-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={onChangeSchool}
          >
            학교 다시 선택
          </button>
        </div>
      </div>

      <div className="bento-card date-selection-picker">
        <DateRangePicker range={range} onChange={setRange} />
      </div>

      {!validation.valid ? (
        <StatusPanel
          tone="error"
          title="날짜 범위를 확인해 주세요"
          description={validation.message}
        />
      ) : null}

      <button
        type="button"
        className="primary-button"
        onClick={handleSubmit}
        disabled={!validation.valid}
      >
        급식 조회
      </button>
    </section>
  )
}
