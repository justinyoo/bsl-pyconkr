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
            {meal.dishes.map((dish, index) => (
              <li key={`${dish}-${index}`}>{dish}</li>
            ))}
          </ul>
          {meal.calories ? (
            <p className="meal-card__metadata">
              <strong>열량</strong> {meal.calories}
            </p>
          ) : null}
          {meal.servingCount !== null ? (
            <p className="meal-card__metadata">
              <strong>급식 인원</strong>{' '}
              {meal.servingCount.toLocaleString('ko-KR')}명
            </p>
          ) : null}
          <MealInformation title="원산지" items={meal.origins} />
          <MealInformation title="영양 정보" items={meal.nutrition} />
        </>
      ) : (
        <p className="meal-card__empty">급식 정보 없음</p>
      )}
    </article>
  )
}

function MealInformation({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) {
    return null
  }

  return (
    <section className="meal-card__information">
      <h4>{title}</h4>
      <ul>
        {items.map((item, index) => (
          <li key={`${item}-${index}`}>{item}</li>
        ))}
      </ul>
    </section>
  )
}
