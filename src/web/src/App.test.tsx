import { describe, expect, it } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'
import { renderWithProviders } from './test/renderWithProviders'

describe('App (school search -> date selection -> results flow)', () => {
  it('lets a user search for a school, pick a date range, and see lunch meals', async () => {
    const user = userEvent.setup()
    window.history.replaceState(null, '', '/legacy?school=서울고')
    renderWithProviders(<App />)

    await waitFor(() => {
      expect(window.location.pathname).toBe('/')
      expect(window.location.search).toBe('')
    })

    const searchInput = screen.getByRole('searchbox', {
      name: '학교 이름으로 검색',
    })
    await user.type(searchInput, '서울고')

    const schoolButton = await screen.findByRole('button', {
      name: /서울고등학교/,
    })
    await user.click(schoolButton)
    expect(window.location.href).toBe('http://localhost:3000/')

    expect(
      await screen.findByRole('heading', { name: '서울고등학교' }),
    ).toBeInTheDocument()

    const submitButton = screen.getByRole('button', { name: '급식 조회' })
    expect(submitButton).toBeEnabled()
    await user.click(submitButton)
    expect(window.location.href).toBe('http://localhost:3000/')

    expect(await screen.findByText('현미밥')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '날짜 다시 선택' }))
    expect(
      screen.getByRole('heading', { name: '서울고등학교' }),
    ).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '학교 다시 선택' }))
    expect(
      screen.getByRole('searchbox', { name: '학교 이름으로 검색' }),
    ).toBeInTheDocument()
    expect(window.location.href).toBe('http://localhost:3000/')
  })
})
