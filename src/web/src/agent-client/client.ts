import { HttpAgent } from '@ag-ui/client'

import type {
  BattleEvaluation,
  EvaluationRequest,
  EvaluationSchool,
  EvaluationStep,
  ProgressHandler,
} from './types'

const STEP_BY_EXECUTOR: Record<string, EvaluationStep> = {
  prepare_evaluation: 'prepare',
  nutrition_balance_evaluator: 'nutrition_balance',
  healthiness_evaluator: 'healthiness',
  menu_quality_evaluator: 'menu_quality',
  score_evaluation: 'score',
  final_evaluator: 'final',
}

export async function getRandomSchools(
  signal?: AbortSignal,
): Promise<EvaluationSchool[]> {
  const response = await fetch('/agent-api/schools/random?count=10', { signal })
  if (!response.ok) {
    throw new Error('분석 후보 학교를 불러오지 못했습니다.')
  }

  const payload = (await response.json()) as { schools?: EvaluationSchool[] }
  if (!Array.isArray(payload.schools) || payload.schools.length !== 10) {
    throw new Error('서로 다른 후보 학교 10개를 준비하지 못했습니다.')
  }
  return payload.schools
}

function stepFromEvent(event: {
  stepName?: string
  name?: string
}): EvaluationStep | undefined {
  const key = event.stepName ?? event.name
  return key ? STEP_BY_EXECUTOR[key] : undefined
}

export function toNaturalEvaluationInput(request: EvaluationRequest): string {
  const schoolLabel = (school: EvaluationSchool) =>
    `${school.schoolName}(${school.locationName ?? school.educationOfficeName})`
  const prefix = `${request.date}의 ${schoolLabel(request.schools[0])}과 ${schoolLabel(request.schools[1])} 중식을`
  const prompt = request.prompt.trim()
  return prompt.startsWith(prefix)
    ? prompt
    : `${prefix} 평가해 주세요. 추가 요청: ${prompt}`
}

export async function runEvaluation(
  request: EvaluationRequest,
  onProgress: ProgressHandler,
): Promise<BattleEvaluation> {
  let runErrorMessage: string | null = null
  const agent = new HttpAgent({
    url: '/ag-ui/evaluate',
    initialMessages: [
      {
        id: crypto.randomUUID(),
        role: 'user',
        content: toNaturalEvaluationInput(request),
      },
    ],
  })

  let run
  try {
    run = await agent.runAgent(
      {},
      {
        onStepStartedEvent: ({ event }) => {
          const step = stepFromEvent(event)
          if (step) onProgress(step, 'running')
        },
        onStepFinishedEvent: ({ event }) => {
          const step = stepFromEvent(event)
          if (step) onProgress(step, 'done')
        },
        onRunErrorEvent: ({ event }) => {
          runErrorMessage = event.message
        },
      },
    )
  } catch (error) {
    if (runErrorMessage?.includes('선택한 기간에 중식 정보가 없습니다.')) {
      throw new Error(
        '선택한 학교 중 해당 날짜의 중식 정보가 없는 학교가 있습니다. 다른 학교나 날짜를 선택해 주세요.',
      )
    }
    if (runErrorMessage) {
      throw new Error(runErrorMessage)
    }
    throw error
  }

  const finalMessage = [...run.newMessages]
    .reverse()
    .find(
      (message) =>
        message.role === 'assistant' && typeof message.content === 'string',
    )
  const raw =
    typeof run.result === 'string'
      ? run.result
      : finalMessage && typeof finalMessage.content === 'string'
        ? finalMessage.content
        : JSON.stringify(run.result)
  try {
    return JSON.parse(raw) as BattleEvaluation
  } catch {
    throw new Error('분석 결과 형식을 확인할 수 없습니다.')
  }
}
