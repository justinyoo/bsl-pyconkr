import type { Meal } from '../api-client/client'
import { isoToLocalDate, localDateToIso } from './dateRange'

export interface DailyMealEntry {
  date: string
  meal?: Meal
}

/**
 * `from`~`to` 사이의 모든 날짜를 채우고, 급식 데이터가 없는 날짜는
 * `meal: undefined`로 남겨 "급식 정보 없음" 카드로 렌더링할 수 있게 한다
 * (PRD MVP 정책: 빈 날짜도 결과에 표시).
 */
export function fillMissingDates(
  from: string,
  to: string,
  meals: Meal[],
): DailyMealEntry[] {
  const mealsByDate = new Map(meals.map((meal) => [meal.date, meal]))
  const entries: DailyMealEntry[] = []

  const cursor = isoToLocalDate(from)
  const end = isoToLocalDate(to)
  while (cursor.getTime() <= end.getTime()) {
    const iso = localDateToIso(cursor)
    entries.push({ date: iso, meal: mealsByDate.get(iso) })
    cursor.setDate(cursor.getDate() + 1)
  }

  return entries
}
