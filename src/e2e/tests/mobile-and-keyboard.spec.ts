import { expect, test } from '@playwright/test'
import { FIXTURE_SCHOOL_NAME, FIXTURE_SEARCH_QUERY } from './fixtures'

test.describe('모바일 반응형과 키보드 접근성', () => {
  test('모바일 뷰포트에서 가로 스크롤 없이 전체 흐름을 완료할 수 있다', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/')

    async function assertNoHorizontalOverflow() {
      const { scrollWidth, clientWidth } = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }))
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth)
    }

    await assertNoHorizontalOverflow()

    await page.getByLabel('학교 이름으로 검색').fill(FIXTURE_SEARCH_QUERY)
    const resultCard = page.getByRole('button', { name: new RegExp(FIXTURE_SCHOOL_NAME) })
    await expect(resultCard).toBeVisible()
    await assertNoHorizontalOverflow()

    await resultCard.click()
    await expect(page).toHaveURL('/')
    await expect(page.getByRole('heading', { name: FIXTURE_SCHOOL_NAME })).toBeVisible()
    await assertNoHorizontalOverflow()

    await page.getByRole('button', { name: '급식 조회' }).click()
    await expect(page).toHaveURL('/')
    await expect(page.locator('.meal-card').first()).toBeVisible()
    await assertNoHorizontalOverflow()
  })

  test('키보드만으로 검색, 학교 선택, 급식 조회까지 완료할 수 있다', async ({
    page,
  }) => {
    await page.goto('/')

    // 검색창에 포커스해 학교 이름 일부를 입력한다.
    await page.getByLabel('학교 이름으로 검색').focus()
    await page.keyboard.type(FIXTURE_SEARCH_QUERY)

    const resultCard = page.getByRole('button', { name: new RegExp(FIXTURE_SCHOOL_NAME) })
    await expect(resultCard).toBeVisible()

    // Tab으로 검색 결과 버튼까지 이동해 Enter로 선택한다.
    await resultCard.focus()
    await expect(resultCard).toBeFocused()
    await page.keyboard.press('Enter')
    await expect(page).toHaveURL('/')

    await expect(page.getByRole('heading', { name: FIXTURE_SCHOOL_NAME })).toBeVisible()

    // 급식 조회 버튼까지 Tab으로 이동해 Enter로 제출한다.
    const submitButton = page.getByRole('button', { name: '급식 조회' })
    await submitButton.focus()
    await expect(submitButton).toBeFocused()
    await page.keyboard.press('Enter')
    await expect(page).toHaveURL('/')

    await expect(page.locator('.meal-card').first()).toBeVisible()
  })
})
