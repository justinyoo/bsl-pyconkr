import { useId, useState, type FormEvent } from 'react'
import { MIN_SCHOOL_QUERY_LENGTH } from '../hooks/useSchoolSearch'

interface SchoolSearchFormProps {
  value: string
  onChange: (value: string) => void
}

/**
 * 학교명 검색 입력. 폼 제출을 막아 Enter로도 자연스럽게 동작하게 하고,
 * 최소 글자 수 안내를 실시간으로 보여준다(FR-01~03).
 */
export function SchoolSearchForm({ value, onChange }: SchoolSearchFormProps) {
  const inputId = useId()
  const hintId = useId()
  const [touched, setTouched] = useState(false)

  const trimmedLength = value.trim().length
  const showHint = touched && trimmedLength > 0 && trimmedLength < MIN_SCHOOL_QUERY_LENGTH

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
  }

  return (
    <form
      className="bento-card school-search-form"
      onSubmit={handleSubmit}
      role="search"
    >
      <label className="school-search-form__label" htmlFor={inputId}>
        학교 이름으로 검색
      </label>
      <input
        id={inputId}
        type="search"
        inputMode="search"
        autoComplete="off"
        placeholder="예: 서울고등학교"
        value={value}
        onChange={(event) => {
          onChange(event.target.value)
          setTouched(true)
        }}
        aria-describedby={hintId}
        className="school-search-form__input"
      />
      <p id={hintId} className="school-search-form__hint" aria-live="polite">
        {showHint
          ? `${MIN_SCHOOL_QUERY_LENGTH}자 이상 입력해 주세요.`
          : '학교 이름의 일부만 입력해도 검색할 수 있어요.'}
      </p>
    </form>
  )
}
