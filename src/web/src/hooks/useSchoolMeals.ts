import { useQuery } from '@tanstack/react-query'
import { getSchoolMeals } from '../api-client/client'

interface UseSchoolMealsParams {
  schoolCode: string
  officeCode: string
  from: string
  to: string
  enabled: boolean
}

export function useSchoolMeals({
  schoolCode,
  officeCode,
  from,
  to,
  enabled,
}: UseSchoolMealsParams) {
  return useQuery({
    queryKey: ['schools', schoolCode, 'meals', officeCode, from, to],
    queryFn: () => getSchoolMeals({ schoolCode, officeCode, from, to }),
    enabled,
  })
}
