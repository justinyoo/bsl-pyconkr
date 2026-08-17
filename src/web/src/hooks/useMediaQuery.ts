import { useEffect, useState } from 'react'

/**
 * 지정한 미디어 쿼리가 일치하는지 반환한다. `window.matchMedia`가 없는
 * 테스트 환경(JSDOM 기본값)에서는 항상 `false`로 취급해 안전하게 동작한다.
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return false
    }
    return window.matchMedia(query).matches
  })

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return
    }
    const mediaQueryList = window.matchMedia(query)
    const listener = () => setMatches(mediaQueryList.matches)
    listener()
    mediaQueryList.addEventListener('change', listener)
    return () => mediaQueryList.removeEventListener('change', listener)
  }, [query])

  return matches
}
