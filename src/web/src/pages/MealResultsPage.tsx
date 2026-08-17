import type { SchoolSummary } from '../api-client/client'
import { StatusPanel } from '../components/StatusPanel'
import { MealCard } from '../components/MealCard'
import { useSchoolMeals } from '../hooks/useSchoolMeals'
import { validateDateRange } from '../lib/dateRange'
import { isoToLocalDate } from '../lib/dateRange'
import { fillMissingDates } from '../lib/fillMissingDates'
import { ApiRequestError, NetworkRequestError } from '../api-client/client'

interface MealResultsPageProps {
  school: SchoolSummary
  from: string
  to: string
  onChangeSchool: () => void
  onChangeDates: () => void
}

export function MealResultsPage({
  school,
  from,
  to,
  onChangeSchool,
  onChangeDates,
}: MealResultsPageProps) {
  const validation = validateDateRange(isoToLocalDate(from), isoToLocalDate(to))

  const { data, isLoading, isError, error } = useSchoolMeals({
    schoolCode: school.schoolCode,
    officeCode: school.educationOfficeCode,
    from,
    to,
    enabled: validation.valid,
  })

  return (
    <section className="bento-grid bento-grid--results">
      <div className="bento-card meal-results-summary">
        <p className="meal-results-summary__eyebrow">조회한 학교</p>
        <h2>{school.schoolName}</h2>
        <p>
          {from} ~ {to}
        </p>
        <div className="flow-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={onChangeSchool}
          >
            학교 다시 선택
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={onChangeDates}
          >
            날짜 다시 선택
          </button>
        </div>
      </div>

      {!validation.valid ? (
        <StatusPanel
          tone="error"
          title="날짜 범위를 확인해 주세요"
          description={validation.message}
        />
      ) : null}

      {validation.valid && isLoading ? (
        <StatusPanel tone="loading" title="급식 정보를 불러오는 중이에요…" />
      ) : null}

      {validation.valid && isError ? (
        <StatusPanel
          tone="error"
          title="급식 정보를 불러오지 못했어요"
          description={describeError(error)}
        />
      ) : null}

      {validation.valid && data ? (
        <div className="meal-results-grid">
          {fillMissingDates(from, to, data.meals).map(({ date, meal }) => (
            <MealCard key={date} date={date} meal={meal} />
          ))}
        </div>
      ) : null}
    </section>
  )
}

function describeError(error: unknown): string {
  if (error instanceof ApiRequestError) {
    return error.problem.detail ?? error.problem.title
  }
  if (error instanceof NetworkRequestError) {
    return error.message
  }
  return '알 수 없는 오류가 발생했습니다.'
}
