import { expect, test } from '@playwright/test'
import { FIXTURE_SCHOOL_NAME, searchAndSelectFixtureSchool } from './fixtures'

test.describe('학교 급식 조회 핵심 흐름', () => {
  test('학교명 일부 검색부터 급식 결과 확인까지 전체 흐름이 동작한다', async ({
    page,
  }) => {
    // 1~2. 학교명 일부 입력 후 검색 결과에서 학교 선택
    await searchAndSelectFixtureSchool(page)
    await expect(page).toHaveURL('/')

    // 3. Date Picker의 유효한 기본 범위가 이미 선택되어 있는지 확인
    const dateGrid = page.locator('[aria-label="급식 조회 날짜 범위 선택"]')
    await expect(dateGrid).toBeVisible()

    const submitButton = page.getByRole('button', { name: '급식 조회' })
    await expect(submitButton).toBeEnabled()

    // 4. 급식 조회
    await submitButton.click()
    await expect(page).toHaveURL('/')

    // 5. 날짜별 메뉴와 급식 없음 카드 확인
    await expect(page.getByRole('heading', { name: FIXTURE_SCHOOL_NAME })).toBeVisible()
    await expect(page.locator('.meal-card').first()).toBeVisible()

    const emptyCards = page.locator('.meal-card', { hasText: '급식 정보 없음' })
    await expect(emptyCards.first()).toBeVisible()

    const populatedCards = page.locator('.meal-card__dishes')
    await expect(populatedCards.first()).toBeVisible()

    await page.getByRole('button', { name: '날짜 다시 선택' }).click()
    await expect(dateGrid).toBeVisible()
    await page.getByRole('button', { name: '학교 다시 선택' }).click()
    await expect(page.getByLabel('학교 이름으로 검색')).toBeVisible()
    await expect(page).toHaveURL('/')
  })

  test('검색어가 2자 미만이면 안내만 표시되고 결과를 조회하지 않는다', async ({
    page,
  }) => {
    await page.goto('/')
    await page.getByLabel('학교 이름으로 검색').fill('서')

    await expect(page.getByText('2자 이상 입력해 주세요.')).toBeVisible()
    await expect(page.getByRole('list', { name: '학교 검색 결과' })).toHaveCount(0)
  })

  test('일치하는 학교가 없으면 빈 결과 상태를 보여준다', async ({ page }) => {
    await page.goto('/')
    await page.getByLabel('학교 이름으로 검색').fill('존재하지않는학교이름')

    await expect(page.getByText('검색 결과가 없어요')).toBeVisible()
  })
})
