import { http, HttpResponse } from 'msw'
import type { components } from '../../api-client/schema'

type SchoolSummary = components['schemas']['SchoolSummary']
type MealRangeResponse = components['schemas']['MealRangeResponse']

export const SEOUL_HIGH_SCHOOL: SchoolSummary = {
  schoolCode: '7010113',
  educationOfficeCode: 'B10',
  schoolName: '서울고등학교',
  educationOfficeName: '서울특별시교육청',
  locationName: '서울특별시',
  schoolType: '고등학교',
}

export const SAMPLE_MEAL_RESPONSE: MealRangeResponse = {
  school: {
    schoolCode: SEOUL_HIGH_SCHOOL.schoolCode,
    educationOfficeCode: SEOUL_HIGH_SCHOOL.educationOfficeCode,
    schoolName: SEOUL_HIGH_SCHOOL.schoolName,
    educationOfficeName: SEOUL_HIGH_SCHOOL.educationOfficeName,
  },
  from: '2024-01-01',
  to: '2024-01-02',
  meals: [
    {
      date: '2024-01-02',
      mealType: 'lunch',
      dishes: ['현미밥', '미역국', '제육볶음'],
      origins: ['쌀: 국내산'],
      nutrition: ['탄수화물(g): 92.1'],
      calories: '742.3 Kcal',
      servingCount: 530,
    },
  ],
}

// 노드 환경의 fetch에는 브라우저 `location`이 없어 MSW가 상대 경로
// 핸들러의 origin을 추론하지 못한다. 테스트에서 사용하는 절대 base URL과
// 동일한 값을 사용해 핸들러를 등록한다(`.env.test`의 `VITE_API_BASE_URL`).
const API_BASE = 'http://localhost/api/v1'

export const handlers = [
  http.get(`${API_BASE}/schools`, ({ request }) => {
    const url = new URL(request.url)
    const name = url.searchParams.get('name') ?? ''
    if (name.trim().length < 2) {
      return HttpResponse.json(
        {
          type: 'https://example.invalid/problems/invalid-request',
          title: 'Invalid request',
          status: 400,
          code: 'INVALID_REQUEST',
          detail: '검색어는 2자 이상 입력해야 합니다.',
        },
        { status: 400 },
      )
    }
    if (!name.includes('서울')) {
      return HttpResponse.json({ items: [], total: 0 })
    }
    return HttpResponse.json({ items: [SEOUL_HIGH_SCHOOL], total: 1 })
  }),

  http.get(`${API_BASE}/schools/:schoolCode/meals`, ({ request }) => {
    const url = new URL(request.url)
    const from = url.searchParams.get('from') ?? SAMPLE_MEAL_RESPONSE.from
    const to = url.searchParams.get('to') ?? SAMPLE_MEAL_RESPONSE.to
    return HttpResponse.json({
      ...SAMPLE_MEAL_RESPONSE,
      from,
      to,
      meals: SAMPLE_MEAL_RESPONSE.meals.map((meal) => ({ ...meal, date: to })),
    })
  }),
]
