import { useQuery } from '@tanstack/react-query'
import { searchSchools } from '../api-client/client'

export const MIN_SCHOOL_QUERY_LENGTH = 2

/** 검색어를 다듬어 최소 길이를 만족할 때만 백엔드 검색을 실행한다. */
export function useSchoolSearch(rawQuery: string) {
  const trimmed = rawQuery.trim()
  const isQueryValid = trimmed.length >= MIN_SCHOOL_QUERY_LENGTH

  const query = useQuery({
    queryKey: ['schools', 'search', trimmed],
    queryFn: () => searchSchools(trimmed),
    enabled: isQueryValid,
  })

  return { ...query, trimmed, isQueryValid }
}
