import { expect, test } from '@playwright/test'

test('두 학교를 선택해 멀티에이전트 분석 결과를 확인한다', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: '급식 분석' }).click()

  const schoolOptions = page.locator('.school-option')
  await expect(schoolOptions).toHaveCount(10)
  await schoolOptions.nth(0).click()
  await schoolOptions.nth(1).click()

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
