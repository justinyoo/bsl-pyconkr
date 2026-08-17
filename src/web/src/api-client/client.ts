/**
 * 백엔드 전용 타입 API 클라이언트.
 *
 * `src/openapi.json`에서 생성된 타입(`schema.d.ts`)을 사용해 요청/응답
 * 형태를 컴파일 타임에 검증한다. 프론트엔드는 NEIS를 직접 호출하지 않고
 * 항상 이 클라이언트를 통해 백엔드(`/api/v1`)를 호출한다.
 */

import createClient from 'openapi-fetch'
import type { components, paths } from './schema'

type ProblemDetail = components['schemas']['ProblemDetail']
export type SchoolSummary = components['schemas']['SchoolSummary']
export type Meal = components['schemas']['Meal']

/** 백엔드가 반환한 `ProblemDetail` 오류를 감싸는 애플리케이션 예외. */
export class ApiRequestError extends Error {
  readonly problem: ProblemDetail

  constructor(problem: ProblemDetail) {
    super(problem.detail ?? problem.title)
    this.name = 'ApiRequestError'
    this.problem = problem
  }
}

/** 네트워크 자체가 실패했을 때(백엔드 연결 불가 등) 사용하는 예외. */
export class NetworkRequestError extends Error {
  constructor(cause: unknown) {
    super('서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.')
    this.name = 'NetworkRequestError'
    this.cause = cause
  }
}

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

const client = createClient<paths>({
  baseUrl,
  // openapi-fetch caches `globalThis.fetch` as a default parameter at
  // client-creation time. In tests, MSW patches `globalThis.fetch` only once
  // its Node server starts listening, which can happen after this module is
  // first imported. Looking `fetch` up lazily on every call keeps requests
  // routed through whatever the current global fetch is (real in the
  // browser, MSW-patched in tests).
  fetch: (...args: Parameters<typeof globalThis.fetch>) => globalThis.fetch(...args),
})

async function unwrap<T>(promise: Promise<{
  data?: T
  error?: ProblemDetail
  response: Response
}>): Promise<T> {
  let result: Awaited<typeof promise>
  try {
    result = await promise
  } catch (cause) {
    throw new NetworkRequestError(cause)
  }
  if (result.error) {
    throw new ApiRequestError(result.error)
  }
  if (result.data === undefined) {
    throw new NetworkRequestError(new Error('empty response body'))
  }
  return result.data
}

export function searchSchools(name: string) {
  return unwrap(
    client.GET('/schools', {
      params: { query: { name } },
    }),
  )
}

interface GetSchoolMealsParams {
  schoolCode: string
  officeCode: string
  from: string
  to: string
}

export function getSchoolMeals({
  schoolCode,
  officeCode,
  from,
  to,
}: GetSchoolMealsParams) {
  return unwrap(
    client.GET('/schools/{schoolCode}/meals', {
      params: {
        path: { schoolCode },
        query: { officeCode, from, to },
      },
    }),
  )
}
