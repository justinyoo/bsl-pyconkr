import { useState } from 'react'
import { SchoolSearchForm } from '../components/SchoolSearchForm'
import { SchoolResultsList } from '../components/SchoolResultsList'
import { StatusPanel } from '../components/StatusPanel'
import { useSchoolSearch } from '../hooks/useSchoolSearch'
import type { SchoolSummary } from '../api-client/client'
import { ApiRequestError, NetworkRequestError } from '../api-client/client'

interface SchoolSearchPageProps {
  onSelect: (school: SchoolSummary) => void
}

export function SchoolSearchPage({ onSelect }: SchoolSearchPageProps) {
  const [query, setQuery] = useState('')
  const { data, isQueryValid, isLoading, isError, error, refetch } =
    useSchoolSearch(query)

  return (
    <section className="bento-grid bento-grid--search">
      <SchoolSearchForm value={query} onChange={setQuery} />

      {isQueryValid && isLoading ? (
        <StatusPanel tone="loading" title="학교를 찾는 중이에요…" />
      ) : null}

      {isQueryValid && isError ? (
        <StatusPanel
          tone="error"
          title="검색 중 문제가 발생했어요"
          description={describeError(error)}
        >
          <button
            type="button"
            className="secondary-button"
            onClick={() => void refetch()}
          >
            다시 시도
          </button>
        </StatusPanel>
      ) : null}

      {isQueryValid && data && data.items.length === 0 ? (
        <StatusPanel
          tone="empty"
          title="검색 결과가 없어요"
          description="학교 이름을 다시 확인해 주세요."
        />
      ) : null}

      {isQueryValid && data && data.items.length > 0 ? (
        <SchoolResultsList schools={data.items} onSelect={onSelect} />
      ) : null}
    </section>
  )
}

function describeError(error: unknown): string {
  if (error instanceof ApiRequestError) {
    return error.problem.detail ?? error.problem.title
  }
  if (error instanceof NetworkRequestError) {
    return error.message
  }
  return '알 수 없는 오류가 발생했습니다.'
}
