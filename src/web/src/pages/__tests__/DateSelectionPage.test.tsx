import { describe, expect, it, vi } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DateSelectionPage } from '../DateSelectionPage'
import { renderWithProviders } from '../../test/renderWithProviders'
import { localDateToIso, todayKst } from '../../lib/dateRange'
import { SEOUL_HIGH_SCHOOL } from '../../test/mocks/handlers'

describe('DateSelectionPage', () => {
  it('shows the selected school and submits the default valid range', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    renderWithProviders(
      <DateSelectionPage
        school={SEOUL_HIGH_SCHOOL}
        onChangeSchool={vi.fn()}
        onSubmit={onSubmit}
      />,
    )

    expect(
      screen.getByRole('heading', { name: '서울고등학교' }),
    ).toBeInTheDocument()
    const submit = screen.getByRole('button', { name: '급식 조회' })
    expect(submit).toBeEnabled()

    await user.click(submit)
    expect(onSubmit).toHaveBeenCalledWith({
      from: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
      to: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
    })
  })

  it('disables submit and explains an invalid reversed date range', () => {
    const today = todayKst()
    const todayDate = new Date(today.year, today.month - 1, today.day)
    const oldDate = new Date(2000, 0, 1)

    renderWithProviders(
      <DateSelectionPage
        school={SEOUL_HIGH_SCHOOL}
        initialRange={{ from: todayDate, to: oldDate }}
        onChangeSchool={vi.fn()}
        onSubmit={vi.fn()}
      />,
    )

    expect(localDateToIso(todayDate)).not.toBe(localDateToIso(oldDate))
    expect(screen.getByText('날짜 범위를 확인해 주세요')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '급식 조회' })).toBeDisabled()
  })
})
