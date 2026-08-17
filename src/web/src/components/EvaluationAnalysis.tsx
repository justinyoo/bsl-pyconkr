import { useEffect, useState } from 'react'

import { getRandomSchools, runEvaluation } from '../agent-client/client'
import type {
  BattleEvaluation,
  EvaluationSchool,
  EvaluationStep,
} from '../agent-client/types'
import { DatePicker } from './DateRangePicker'
import { isoToLocalDate, localDateToIso } from '../lib/dateRange'
import { getEvaluationDateBounds } from '../lib/evaluationDate'

const CRITERIA = {
  nutrition_balance: { label: '영양 균형', weight: 45 },
  healthiness: { label: '건강성', weight: 30 },
  menu_quality: { label: '식재료 및 메뉴 품질', weight: 25 },
} as const

const STEPS: Array<{ id: EvaluationStep; label: string }> = [
  { id: 'prepare', label: '급식 데이터 준비' },
  { id: 'nutrition_balance', label: '영양 균형 평가' },
  { id: 'healthiness', label: '건강성 평가' },
  { id: 'menu_quality', label: '메뉴 품질 평가' },
  { id: 'score', label: '가중 점수 계산' },
  { id: 'final', label: '최종 품질 검증' },
]

function defaultPrompt(
  schools: EvaluationSchool[],
  selected: string[],
  date: string,
) {
  const names = selected
    .map((code) => schools.find((school) => school.schoolCode === code))
    .filter((school): school is EvaluationSchool => Boolean(school))
    .map(
      (school) =>
        `${school.schoolName}(${school.locationName ?? school.educationOfficeName})`,
    )
  return names.length === 2
    ? `${date}의 ${names[0]}과 ${names[1]} 중식을 평가 루브릭에 따라 비교해 주세요. 확인 가능한 NEIS 데이터만 근거로 사용하고, 각 학교의 개선안을 제시해 주세요.`
    : '비교할 두 학교와 날짜를 선택하면 분석 요청문이 만들어집니다.'
}

function ResultPanel({ result }: { result: BattleEvaluation }) {
  const winner =
    result.outcome === 'tie' || result.outcome === 'incomplete'
      ? null
      : result.schoolScores.find(
          (score) => score.school.schoolCode === result.winnerSchoolCode,
        )

  return (
    <section className="evaluation-results" aria-live="polite">
      <div className="winner-card">
        <p className="section-kicker">최종 판정</p>
        <h2>
          {result.outcome === 'incomplete'
            ? '급식 정보 부족으로 승패를 보류합니다'
            : winner
              ? `${winner.school.schoolName} 승리`
              : '두 학교가 동점입니다'}
        </h2>
        <p>{result.summary}</p>
      </div>

      <div className="score-grid">
        {result.unavailableSchools.map((school) => (
          <article
            className="school-score-card unavailable-school-card"
            key={school.schoolCode}
          >
            <header>
              <p>{school.educationOfficeName}</p>
              <h3>{school.schoolName}</h3>
              <strong>분석 불가</strong>
            </header>
            <p>
              선택한 날짜의 중식 정보가 없어 이 학교는 분석할 수 없습니다.
            </p>
          </article>
        ))}
        {result.schoolScores.map((score) => (
          <article className="school-score-card" key={score.school.schoolCode}>
            <header>
              <p>{score.school.educationOfficeName}</p>
              <h3>{score.school.schoolName}</h3>
              <strong>{score.totalScore.toFixed(1)}점</strong>
            </header>
            {score.criteria.map((criterion) => {
              const meta = CRITERIA[criterion.criterion]
              return (
                <section
                  className="criterion-result"
                  key={criterion.criterion}
                >
                  <div className="criterion-heading">
                    <h4>{meta.label}</h4>
                    <span>
                      {criterion.rating}/5 ·{' '}
                      {criterion.weightedScore.toFixed(1)}/{meta.weight}
                    </span>
                  </div>
                  <p>
                    <strong>근거</strong> {criterion.evidence.join(' · ')}
                  </p>
                  {criterion.limitations.length > 0 ? (
                    <p>
                      <strong>한계</strong>{' '}
                      {criterion.limitations.join(' · ')}
                    </p>
                  ) : null}
                  <p>
                    <strong>개선</strong>{' '}
                    {criterion.improvements.join(' · ')}
                  </p>
                </section>
              )
            })}
          </article>
        ))}
      </div>

      <div className="result-notes">
        <section>
          <h3>핵심 이유</h3>
          <ul>
            {result.keyReasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </section>
        <section>
          <h3>학교별 최종 개선안</h3>
          {result.schoolScores.map((score) => (
            <div key={score.school.schoolCode}>
              <h4>{score.school.schoolName}</h4>
              <ul>
                {(result.improvements[score.school.schoolCode] ?? []).map(
                  (improvement) => (
                    <li key={improvement}>{improvement}</li>
                  ),
                )}
              </ul>
            </div>
          ))}
        </section>
        {result.warnings.length > 0 ? (
          <section className="warning-note">
            <h3>데이터 한계</h3>
            <ul>
              {result.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </section>
  )
}

export function EvaluationAnalysis() {
  const [schools, setSchools] = useState<EvaluationSchool[]>([])
  const [selected, setSelected] = useState<string[]>([])
  const [date, setDate] = useState(() => getEvaluationDateBounds().max)
  const [prompt, setPrompt] = useState('')
  const [promptEdited, setPromptEdited] = useState(false)
  const [loadingSchools, setLoadingSchools] = useState(true)
  const [running, setRunning] = useState(false)
  const [steps, setSteps] = useState<
    Partial<Record<EvaluationStep, 'running' | 'done'>>
  >({})
  const [result, setResult] = useState<BattleEvaluation | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getRandomSchools(controller.signal)
      .then(setSchools)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === 'AbortError') return
        setError(
          reason instanceof Error
            ? reason.message
            : '학교를 불러오지 못했습니다.',
        )
      })
      .finally(() => setLoadingSchools(false))
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!promptEdited) {
      setPrompt(defaultPrompt(schools, selected, date))
    }
  }, [date, promptEdited, schools, selected])

  const toggleSchool = (schoolCode: string) => {
    setSelected((current) => {
      if (current.includes(schoolCode)) {
        return current.filter((code) => code !== schoolCode)
      }
      return current.length < 2 ? [...current, schoolCode] : current
    })
    setPromptEdited(false)
  }

  const evaluate = async () => {
    const chosen = selected
      .map((code) =>
        schools.find((school) => school.schoolCode === code),
      )
      .filter((school): school is EvaluationSchool => Boolean(school))
    if (chosen.length !== 2) return

    setRunning(true)
    setError(null)
    setResult(null)
    setSteps({})
    try {
      const evaluation = await runEvaluation(
        { schools: [chosen[0], chosen[1]], date, prompt },
        (step, status) =>
          setSteps((current) => ({ ...current, [step]: status })),
      )
      setResult(evaluation)
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : '분석을 완료하지 못했습니다.',
      )
    } finally {
      setRunning(false)
    }
  }

  return (
    <main className="analysis-page">
      <section className="analysis-hero">
        <p className="section-kicker">MULTI-AGENT LUNCH BATTLE</p>
        <h1>
          두 학교의 급식을
          <br />세 관점으로 분석해요.
        </h1>
        <p>
          전문 에이전트가 동시에 평가하고, 계산된 점수는 최종 품질 검증을
          거칩니다.
        </p>
      </section>

      <section className="analysis-controls" aria-labelledby="analysis-settings">
        <h2 id="analysis-settings">분석 조건</h2>
        <div className="analysis-field">
          <div className="field-heading">
            <h3>1. 학교 두 곳 선택</h3>
            <span>{selected.length}/2</span>
          </div>
          {loadingSchools ? (
            <p className="status-message">
              후보 학교 10곳을 준비하고 있습니다.
            </p>
          ) : (
            <div className="school-options">
              {schools.map((school) => (
                <label
                  className={`school-option ${
                    selected.includes(school.schoolCode) ? 'is-selected' : ''
                  }`}
                  key={school.schoolCode}
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(school.schoolCode)}
                    disabled={
                      !selected.includes(school.schoolCode) &&
                      selected.length === 2
                    }
                    onChange={() => toggleSchool(school.schoolCode)}
                  />
                  <span>
                    <strong>{school.schoolName}</strong>
                    <small>
                      {school.locationName ?? school.educationOfficeName}
                    </small>
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="analysis-field">
          <h3>2. 평가 날짜</h3>
          <DatePicker
            mode="single"
            date={isoToLocalDate(date)}
            onChange={(selectedDate) => {
              if (!selectedDate) return
              setDate(localDateToIso(selectedDate))
              setPromptEdited(false)
            }}
          />
        </div>

        <div className="analysis-field">
          <label htmlFor="evaluation-prompt">3. 분석 요청문</label>
          <textarea
            id="evaluation-prompt"
            rows={5}
            maxLength={4000}
            value={prompt}
            onChange={(event) => {
              setPrompt(event.target.value)
              setPromptEdited(true)
            }}
          />
          <small>
            요청문은 수정할 수 있지만 점수 계산 기준과 가중치는 고정됩니다.
          </small>
        </div>

        <button
          className="primary-button analysis-submit"
          type="button"
          disabled={selected.length !== 2 || !prompt.trim() || running}
          onClick={evaluate}
        >
          {running ? '에이전트 분석 중…' : '급식 배틀 시작'}
        </button>
      </section>

      {running || Object.keys(steps).length > 0 ? (
        <section className="workflow-progress" aria-live="polite">
          <h2>분석 진행 상황</h2>
          <ol>
            {STEPS.map((step) => (
              <li
                aria-label={`${step.label}: ${
                  steps[step.id] === 'done'
                    ? '완료'
                    : steps[step.id] === 'running'
                      ? '진행 중'
                      : '대기'
                }`}
                className={steps[step.id] ?? ''}
                key={step.id}
              >
                <span
                  className={
                    steps[step.id] === 'running' ? 'progress-spinner' : ''
                  }
                  aria-hidden="true"
                >
                  {steps[step.id] === 'done'
                    ? '✓'
                    : steps[step.id] === 'running'
                      ? ''
                      : '○'}
                </span>
                {step.label}
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {error ? (
        <p className="error-message analysis-error" role="alert">
          {error}
        </p>
      ) : null}
      {result ? <ResultPanel result={result} /> : null}
    </main>
  )
}
