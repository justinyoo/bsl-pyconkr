import type { Meal } from '../api-client/client'

interface MealCardProps {
  date: string
  meal?: Meal
}

const WEEKDAY_FORMATTER = new Intl.DateTimeFormat('ko-KR', {
  month: 'long',
  day: 'numeric',
  weekday: 'short',
})

function formatDateLabel(iso: string): string {
  const [year, month, day] = iso.split('-').map(Number)
  return WEEKDAY_FORMATTER.format(new Date(year, month - 1, day))
}

/** 날짜별 급식 카드. 데이터가 없는 날짜는 "급식 정보 없음"으로 표시한다(FR-18). */
export function MealCard({ date, meal }: MealCardProps) {
  return (
    <article className="bento-card meal-card">
      <header className="meal-card__header">
        <h3>{formatDateLabel(date)}</h3>
      </header>
      {meal ? (
        <>
          <ul className="meal-card__dishes">
            {meal.dishes.map((dish) => (
              <li key={dish}>{dish}</li>
            ))}
          </ul>
          {meal.calories ? (
            <p className="meal-card__calories">{meal.calories}</p>
          ) : null}
        </>
      ) : (
        <p className="meal-card__empty">급식 정보 없음</p>
      )}
    </article>
  )
}
