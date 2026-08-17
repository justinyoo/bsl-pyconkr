import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type {
  BattleEvaluation,
  EvaluationSchool,
} from '../../agent-client/types'
import { EvaluationAnalysis } from '../EvaluationAnalysis'

const mocks = vi.hoisted(() => ({
  getRandomSchools: vi.fn(),
  runEvaluation: vi.fn(),
}))

vi.mock('../../agent-client/client', () => mocks)

const schools: EvaluationSchool[] = Array.from({ length: 10 }, (_, index) => ({
  schoolCode: `S${index + 1}`,
  educationOfficeCode: 'B10',
  schoolName: `예시학교${index + 1}`,
  educationOfficeName: '서울특별시교육청',
  locationName: '서울특별시',
  schoolType: '고등학교',
}))

const result: BattleEvaluation = {
  date: '2026-08-17',
  schoolScores: [
    {
      school: schools[0],
      totalScore: 60,
      criteria: [
        {
          criterion: 'nutrition_balance',
          rating: 3,
          weight: 45,
          weightedScore: 27,
          evidence: ['영양 근거'],
          limitations: ['영양 한계'],
          improvements: ['영양 개선'],
        },
        {
          criterion: 'healthiness',
          rating: 3,
          weight: 30,
          weightedScore: 18,
          evidence: ['건강 근거'],
          limitations: [],
          improvements: ['건강 개선'],
        },
        {
          criterion: 'menu_quality',
          rating: 3,
          weight: 25,
          weightedScore: 15,
          evidence: ['메뉴 근거'],
          limitations: [],
          improvements: ['메뉴 개선'],
        },
      ],
    },
    {
      school: schools[1],
      totalScore: 80,
      criteria: [
        {
          criterion: 'nutrition_balance',
          rating: 4,
          weight: 45,
          weightedScore: 36,
          evidence: ['영양 근거'],
          limitations: [],
          improvements: ['영양 개선'],
        },
        {
          criterion: 'healthiness',
          rating: 4,
          weight: 30,
          weightedScore: 24,
          evidence: ['건강 근거'],
          limitations: [],
          improvements: ['건강 개선'],
        },
        {
          criterion: 'menu_quality',
          rating: 4,
          weight: 25,
          weightedScore: 20,
          evidence: ['메뉴 근거'],
          limitations: [],
          improvements: ['메뉴 개선'],
        },
      ],
    },
  ],
  unavailableSchools: [],
  outcome: 'second',
  winnerSchoolCode: 'S2',
  summary: '예시학교2의 구성이 더 균형 잡혔습니다.',
  keyReasons: ['세 영역에서 더 높은 평가를 받았습니다.'],
  improvements: { S1: ['채소를 보강합니다.'], S2: ['염도를 확인합니다.'] },
  warnings: ['제공된 데이터만 평가했습니다.'],
}

describe('EvaluationAnalysis', () => {
  beforeEach(() => {
    mocks.getRandomSchools.mockResolvedValue(schools)
    mocks.runEvaluation.mockResolvedValue(result)
  })

  it('selects exactly two schools, keeps the prompt editable, and renders scores', async () => {
    const user = userEvent.setup()
    render(<EvaluationAnalysis />)

    expect(await screen.findAllByRole('checkbox')).toHaveLength(10)
    expect(
      screen.getByLabelText('급식 평가 날짜 선택'),
    ).toBeInTheDocument()
    await user.click(screen.getByText('예시학교1'))
    await user.click(screen.getByText('예시학교2'))

    expect(screen.getAllByRole('checkbox', { checked: false })[0]).toBeDisabled()
    const prompt = screen.getByLabelText('3. 분석 요청문')
    expect(prompt).toHaveValue(
      '2026-08-17의 예시학교1(서울특별시)과 예시학교2(서울특별시) 중식을 평가 루브릭에 따라 비교해 주세요. 확인 가능한 NEIS 데이터만 근거로 사용하고, 각 학교의 개선안을 제시해 주세요.',
    )
    await user.clear(prompt)
    await user.type(prompt, '수정한 분석 요청')
    await user.click(screen.getByRole('button', { name: '급식 배틀 시작' }))

    await waitFor(() => {
      expect(mocks.runEvaluation).toHaveBeenCalledWith(
        expect.objectContaining({
          schools: [schools[0], schools[1]],
          prompt: '수정한 분석 요청',
        }),
        expect.any(Function),
      )
    })
    expect(
      await screen.findByRole('heading', { name: '예시학교2 승리' }),
    ).toBeInTheDocument()
    expect(screen.getByText('60.0점')).toBeInTheDocument()
    expect(screen.getByText('80.0점')).toBeInTheDocument()
    expect(screen.getByText('영양 한계')).toBeInTheDocument()
  })

  it('shows the unavailable school and completes the other school analysis', async () => {
    const user = userEvent.setup()
    mocks.runEvaluation.mockResolvedValue({
      ...result,
      schoolScores: [result.schoolScores[1]],
      unavailableSchools: [schools[0]],
      outcome: 'incomplete',
      winnerSchoolCode: null,
      summary: '한 학교의 급식 정보가 없어 가능한 학교만 분석했습니다.',
      improvements: { S2: ['염도를 확인합니다.'] },
    })
    render(<EvaluationAnalysis />)

    await screen.findAllByRole('checkbox')
    await user.click(screen.getByText('예시학교1'))
    await user.click(screen.getByText('예시학교2'))
    await user.click(screen.getByRole('button', { name: '급식 배틀 시작' }))

    expect(
      await screen.findByRole('heading', {
        name: '급식 정보 부족으로 승패를 보류합니다',
      }),
    ).toBeInTheDocument()
    expect(screen.getByText('분석 불가')).toBeInTheDocument()
    expect(
      screen.getByText(
        '선택한 날짜의 중식 정보가 없어 이 학교는 분석할 수 없습니다.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('80.0점')).toBeInTheDocument()
    expect(screen.queryByText('60.0점')).not.toBeInTheDocument()
  })
})
