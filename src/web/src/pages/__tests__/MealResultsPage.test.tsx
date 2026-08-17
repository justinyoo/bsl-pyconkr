import { describe, expect, it, vi } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { MealResultsPage } from '../MealResultsPage'
import { renderWithProviders } from '../../test/renderWithProviders'
import { server } from '../../test/mocks/server'
import { SEOUL_HIGH_SCHOOL } from '../../test/mocks/handlers'
import { localDateToIso, todayKst } from '../../lib/dateRange'

const today = todayKst()
const TODAY_ISO = localDateToIso(
  new Date(today.year, today.month - 1, today.day),
)
const yesterday = new Date(today.year, today.month - 1, today.day - 1)
const YESTERDAY_ISO = localDateToIso(yesterday)

function renderPage(from = YESTERDAY_ISO, to = TODAY_ISO) {
  return renderWithProviders(
    <MealResultsPage
      school={SEOUL_HIGH_SCHOOL}
      from={from}
      to={to}
      onChangeSchool={vi.fn()}
      onChangeDates={vi.fn()}
    />,
  )
}

describe('MealResultsPage', () => {
  it('shows a validation error for an out-of-range date without calling the API', () => {
    renderPage('2000-01-01', '2000-01-02')

    expect(screen.getByText('날짜 범위를 확인해 주세요')).toBeInTheDocument()
  })

  it('renders meal cards, filling missing days with the empty state', async () => {
    renderPage()

    expect(await screen.findByText('현미밥')).toBeInTheDocument()
    expect(screen.getByText('742.3 Kcal')).toBeInTheDocument()
    expect(screen.getByText('530명')).toBeInTheDocument()
    expect(screen.getByText('쌀: 국내산')).toBeInTheDocument()
    expect(screen.getByText('탄수화물(g): 92.1')).toBeInTheDocument()
    expect(screen.getByText('급식 정보 없음')).toBeInTheDocument()
  })

  it('offers a retry when the backend request fails', async () => {
    let attempts = 0
    server.use(
      http.get('http://localhost/api/v1/schools/:schoolCode/meals', () => {
        attempts += 1
        if (attempts === 1) {
          return HttpResponse.json(
            {
              type: 'https://example.invalid/problems/upstream',
              title: 'Upstream error',
              status: 502,
              code: 'UPSTREAM_ERROR',
              detail: 'NEIS 서버에서 오류가 발생했습니다.',
            },
            { status: 502 },
          )
        }
        return HttpResponse.json({
          school: SEOUL_HIGH_SCHOOL,
          from: YESTERDAY_ISO,
          to: TODAY_ISO,
          meals: [],
        })
      }),
    )

    const user = userEvent.setup()
    renderPage()

    expect(
      await screen.findByText('급식 정보를 불러오지 못했어요'),
    ).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '다시 시도' }))
    expect(await screen.findAllByText('급식 정보 없음')).toHaveLength(2)
  })
})
