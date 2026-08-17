import { describe, expect, it } from 'vitest'

import { toNaturalEvaluationInput } from '../client'
import type { EvaluationRequest } from '../types'

const request: EvaluationRequest = {
  schools: [
    {
      schoolCode: 'one',
      educationOfficeCode: 'B10',
      schoolName: '첫번째학교',
      educationOfficeName: '서울특별시교육청',
      locationName: '서울특별시',
      schoolType: '중학교',
    },
    {
      schoolCode: 'two',
      educationOfficeCode: 'C10',
      schoolName: '두번째학교',
      educationOfficeName: '부산광역시교육청',
      locationName: '부산광역시',
      schoolType: '고등학교',
    },
  ],
  date: '2026-08-14',
  prompt: '채소 구성을 중점적으로 확인해 주세요.',
}

describe('toNaturalEvaluationInput', () => {
  it('wraps a custom instruction with deterministic school and date context', () => {
    expect(toNaturalEvaluationInput(request)).toBe(
      '2026-08-14의 첫번째학교(서울특별시)과 두번째학교(부산광역시) 중식을 평가해 주세요. 추가 요청: 채소 구성을 중점적으로 확인해 주세요.',
    )
  })

  it('preserves an already canonical natural-language prompt', () => {
    const prompt =
      '2026-08-14의 첫번째학교(서울특별시)과 두번째학교(부산광역시) 중식을 평가 루브릭에 따라 비교해 주세요.'

    expect(toNaturalEvaluationInput({ ...request, prompt })).toBe(prompt)
  })
})
