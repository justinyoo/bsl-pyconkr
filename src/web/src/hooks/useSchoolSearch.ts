import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchSchools } from '../api-client/client'

export const MIN_SCHOOL_QUERY_LENGTH = 2
const SEARCH_DEBOUNCE_MS = 300

/** 검색어를 다듬어 최소 길이를 만족할 때만 백엔드 검색을 실행한다. */
export function useSchoolSearch(rawQuery: string) {
  const trimmed = rawQuery.trim()
  const isQueryValid = trimmed.length >= MIN_SCHOOL_QUERY_LENGTH
  const [debouncedQuery, setDebouncedQuery] = useState(trimmed)

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedQuery(trimmed)
    }, SEARCH_DEBOUNCE_MS)

    return () => window.clearTimeout(timer)
  }, [trimmed])

  const isDebouncing = trimmed !== debouncedQuery
  const isDebouncedQueryValid =
    debouncedQuery.length >= MIN_SCHOOL_QUERY_LENGTH

  const query = useQuery({
    queryKey: ['schools', 'search', debouncedQuery],
    queryFn: () => searchSchools(debouncedQuery),
    enabled: isDebouncedQueryValid,
  })

  return {
    ...query,
    data: isDebouncing ? undefined : query.data,
    error: isDebouncing ? null : query.error,
    isError: isDebouncing ? false : query.isError,
    isLoading: isQueryValid && (isDebouncing || query.isLoading),
    trimmed,
    isQueryValid,
  }
}
