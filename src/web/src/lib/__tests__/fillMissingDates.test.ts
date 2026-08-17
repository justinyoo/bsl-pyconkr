import { describe, expect, it } from 'vitest'
import type { Meal } from '../../api-client/client'
import { fillMissingDates } from '../fillMissingDates'

const lunchOn = (date: string): Meal => ({
  date,
  mealType: 'lunch',
  dishes: ['테스트 메뉴'],
  origins: [],
  nutrition: [],
  calories: '500 Kcal',
  servingCount: 100,
})

describe('fillMissingDates', () => {
  it('fills every date in the range, marking missing days as undefined', () => {
    const meals = [lunchOn('2026-08-01'), lunchOn('2026-08-03')]
    const result = fillMissingDates('2026-08-01', '2026-08-03', meals)

    expect(result).toHaveLength(3)
    expect(result[0]).toEqual({ date: '2026-08-01', meal: meals[0] })
    expect(result[1]).toEqual({ date: '2026-08-02', meal: undefined })
    expect(result[2]).toEqual({ date: '2026-08-03', meal: meals[1] })
  })

  it('returns a single entry when from equals to', () => {
    const result = fillMissingDates('2026-08-01', '2026-08-01', [])
    expect(result).toEqual([{ date: '2026-08-01', meal: undefined }])
  })
})
