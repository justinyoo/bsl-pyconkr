import { describe, expect, it } from 'vitest'

import { getEvaluationDateBounds } from '../evaluationDate'

describe('getEvaluationDateBounds', () => {
  it('uses Korea Standard Time across UTC month boundaries', () => {
    expect(
      getEvaluationDateBounds(new Date('2026-03-31T15:30:00.000Z')),
    ).toEqual({
      min: '2026-03-01',
      max: '2026-04-01',
    })
  })

  it('handles the January previous-month year boundary', () => {
    expect(
      getEvaluationDateBounds(new Date('2026-01-15T03:00:00.000Z')),
    ).toEqual({
      min: '2025-12-01',
      max: '2026-01-15',
    })
  })
})
