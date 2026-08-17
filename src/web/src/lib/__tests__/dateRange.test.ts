import { describe, expect, it } from 'vitest'
import {
  allowedRange,
  defaultRange,
  isoToLocalDate,
  localDateToIso,
  validateDateRange,
} from '../dateRange'

const REFERENCE = { year: 2026, month: 8, day: 17 }

describe('allowedRange', () => {
  it('starts at the first day of the previous month and ends today', () => {
    const range = allowedRange(REFERENCE)
    expect(localDateToIso(range.start)).toBe('2026-07-01')
    expect(localDateToIso(range.end)).toBe('2026-08-17')
  })

  it('wraps to December of the previous year in January', () => {
    const range = allowedRange({ year: 2026, month: 1, day: 15 })
    expect(localDateToIso(range.start)).toBe('2025-12-01')
  })
})

describe('defaultRange', () => {
  it('defaults to 7 days before today through today', () => {
    const range = defaultRange(REFERENCE)
    expect(localDateToIso(range.start)).toBe('2026-08-10')
    expect(localDateToIso(range.end)).toBe('2026-08-17')
  })

  it('clamps the default start to the allowed range minimum', () => {
    // 8월 3일 기준 7일 전은 7월 27일이지만, 허용 범위 시작은 7월 1일이라
    // 클램프 없이도 이미 범위 안에 있다. 허용 범위 시작보다 이전으로
    // 가지 않는지 월 초 근처에서 확인한다.
    const range = defaultRange({ year: 2026, month: 8, day: 3 })
    const bounds = allowedRange({ year: 2026, month: 8, day: 3 })
    expect(range.start.getTime()).toBeGreaterThanOrEqual(bounds.start.getTime())
  })
})

describe('validateDateRange', () => {
  it('accepts a range within bounds', () => {
    const result = validateDateRange(
      isoToLocalDate('2026-08-01'),
      isoToLocalDate('2026-08-17'),
      REFERENCE,
    )
    expect(result.valid).toBe(true)
  })

  it('rejects a reversed range', () => {
    const result = validateDateRange(
      isoToLocalDate('2026-08-17'),
      isoToLocalDate('2026-08-01'),
      REFERENCE,
    )
    expect(result.valid).toBe(false)
    expect(result.errorCode).toBe('REVERSED')
  })

  it('rejects a start date before the allowed range', () => {
    const result = validateDateRange(
      isoToLocalDate('2026-06-30'),
      isoToLocalDate('2026-08-01'),
      REFERENCE,
    )
    expect(result.valid).toBe(false)
    expect(result.errorCode).toBe('BEFORE_START')
  })

  it('rejects an end date after today', () => {
    const result = validateDateRange(
      isoToLocalDate('2026-08-01'),
      isoToLocalDate('2026-08-18'),
      REFERENCE,
    )
    expect(result.valid).toBe(false)
    expect(result.errorCode).toBe('AFTER_END')
  })

  it('rejects an incomplete range', () => {
    const result = validateDateRange(undefined, undefined, REFERENCE)
    expect(result.valid).toBe(false)
  })
})

describe('iso <-> local date conversions', () => {
  it('round-trips', () => {
    const date = isoToLocalDate('2026-02-05')
    expect(localDateToIso(date)).toBe('2026-02-05')
  })
})
