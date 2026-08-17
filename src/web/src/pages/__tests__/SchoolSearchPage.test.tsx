import { describe, expect, it, vi } from 'vitest'
import { delay, http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SchoolSearchPage } from '../SchoolSearchPage'
import { renderWithProviders } from '../../test/renderWithProviders'
import { server } from '../../test/mocks/server'
import { SEOUL_HIGH_SCHOOL } from '../../test/mocks/handlers'

describe('SchoolSearchPage', () => {
  it('shows a hint and does not search until the minimum length is reached', async () => {
    const user = userEvent.setup()
    renderWithProviders(<SchoolSearchPage onSelect={vi.fn()} />)

    const input = screen.getByRole('searchbox', { name: '학교 이름으로 검색' })
    await user.type(input, '서')

    expect(await screen.findByText(/2자 이상 입력해 주세요/)).toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  it('renders matching results and lets the user select one', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()
    renderWithProviders(<SchoolSearchPage onSelect={onSelect} />)

    const input = screen.getByRole('searchbox', { name: '학교 이름으로 검색' })
    await user.type(input, '서울고')

    const result = await screen.findByRole('button', { name: /서울고등학교/ })
    expect(result).toBeInTheDocument()
    await user.click(result)
    expect(onSelect).toHaveBeenCalledWith(SEOUL_HIGH_SCHOOL)
  })

  it('shows an empty state when no school matches', async () => {
    const user = userEvent.setup()
    renderWithProviders(<SchoolSearchPage onSelect={vi.fn()} />)

    const input = screen.getByRole('searchbox', { name: '학교 이름으로 검색' })
    await user.type(input, '없는학교')

    expect(await screen.findByText('검색 결과가 없어요')).toBeInTheDocument()
  })

  it('shows a loading status while the search request is in flight', async () => {
    server.use(
      http.get('http://localhost/api/v1/schools', async () => {
        await delay(50)
        return HttpResponse.json({ items: [SEOUL_HIGH_SCHOOL], total: 1 })
      }),
    )
    const user = userEvent.setup()
    renderWithProviders(<SchoolSearchPage onSelect={vi.fn()} />)

    const input = screen.getByRole('searchbox', { name: '학교 이름으로 검색' })
    await user.type(input, '서울고')

    expect(await screen.findByText('학교를 찾는 중이에요…')).toBeInTheDocument()
    expect(
      await screen.findByRole('button', { name: /서울고등학교/ }),
    ).toBeInTheDocument()
  })
})
