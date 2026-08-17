import { expect, type Page } from '@playwright/test'

/** 고정 fixture 모드(`NEIS_FIXTURE_MODE=true`)의 결정적 학교 데이터. */
export const FIXTURE_SCHOOL_NAME = '서울고정예시고등학교'
export const FIXTURE_SEARCH_QUERY = '예시고등'

/**
 * 학교 검색 → 선택 → 날짜 화면 도달까지 공통 단계를 수행한다.
 * 각 테스트가 개별적으로 반복하지 않도록 공유 헬퍼로 둔다.
 */
export async function searchAndSelectFixtureSchool(page: Page): Promise<void> {
  await page.goto('/')
  const searchInput = page.getByLabel('학교 이름으로 검색')
  await searchInput.fill(FIXTURE_SEARCH_QUERY)

  const resultCard = page.getByRole('button', { name: new RegExp(FIXTURE_SCHOOL_NAME) })
  await expect(resultCard).toBeVisible()
  await resultCard.click()

  await expect(page.getByRole('heading', { name: FIXTURE_SCHOOL_NAME })).toBeVisible()
}
