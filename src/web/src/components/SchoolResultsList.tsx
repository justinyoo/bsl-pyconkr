import type { SchoolSummary } from '../api-client/client'

interface SchoolResultsListProps {
  schools: SchoolSummary[]
  onSelect: (school: SchoolSummary) => void
}

/** 검색 결과 목록. 키보드만으로도 학교를 선택할 수 있는 버튼 목록이다. */
export function SchoolResultsList({ schools, onSelect }: SchoolResultsListProps) {
  return (
    <ul className="school-results-list" aria-label="학교 검색 결과">
      {schools.map((school) => (
        <li key={`${school.educationOfficeCode}-${school.schoolCode}`}>
          <button
            type="button"
            className="bento-card school-result-card"
            onClick={() => onSelect(school)}
          >
            <span className="school-result-card__name">{school.schoolName}</span>
            <span className="school-result-card__meta">
              {school.schoolType} · {school.locationName}
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}
