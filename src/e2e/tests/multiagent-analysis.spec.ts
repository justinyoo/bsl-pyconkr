import { expect, test } from '@playwright/test'

test('두 학교를 선택해 멀티에이전트 분석 결과를 확인한다', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: '급식 분석' }).click()

  await expect(page.locator('.school-option')).toHaveCount(10)
  await page.getByText('서울고정예시고등학교', { exact: true }).click()
  await page.getByText('한강예시고등학교', { exact: true }).click()

  const prompt = page.getByLabel('3. 분석 요청문')
  await expect(prompt).toHaveValue(/평가 루브릭/)
  await prompt.fill('fixture 급식을 근거 중심으로 비교해 주세요.')

  await page.getByRole('button', { name: '급식 배틀 시작' }).click()

  await expect(page.getByRole('heading', { name: /승리|동점/ })).toBeVisible({
    timeout: 20_000,
  })
  await expect(page.getByText('60.0점')).toBeVisible()
  await expect(page.getByText('80.0점')).toBeVisible()
  await expect(page.getByRole('heading', { name: '영양 균형' }).first()).toBeVisible()
  await expect(page.getByRole('heading', { name: '건강성' }).first()).toBeVisible()
  await expect(
    page.getByRole('heading', { name: '식재료 및 메뉴 품질' }).first(),
  ).toBeVisible()
})

test('급식이 없는 학교는 표시하고 다른 학교 분석은 완료한다', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: '급식 분석' }).click()

  await expect(page.locator('.school-option')).toHaveCount(10)
  await page.getByText('가온예시고등학교', { exact: true }).click()
  await page.getByText('서울고정예시고등학교', { exact: true }).click()
  await page.getByRole('button', { name: '급식 배틀 시작' }).click()

  await expect(
    page.getByRole('heading', {
      name: '급식 정보 부족으로 승패를 보류합니다',
    }),
  ).toBeVisible({ timeout: 20_000 })
  await expect(
    page.getByText(
      '선택한 날짜의 중식 정보가 없어 이 학교는 분석할 수 없습니다.',
    ),
  ).toBeVisible()
  await expect(page.getByText('60.0점')).toBeVisible()
  await expect(page.getByRole('heading', { name: '영양 균형' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '건강성' })).toBeVisible()
  await expect(
    page.getByRole('heading', { name: '식재료 및 메뉴 품질' }),
  ).toBeVisible()
})
