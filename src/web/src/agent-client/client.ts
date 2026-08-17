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

export async function runEvaluation(
  request: EvaluationRequest,
  onProgress: ProgressHandler,
): Promise<BattleEvaluation> {
  const agent = new HttpAgent({
    url: '/ag-ui/evaluate',
    initialMessages: [
      {
        id: crypto.randomUUID(),
        role: 'user',
        content: JSON.stringify(request),
      },
    ],
  })

  const run = await agent.runAgent(
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
    },
  )

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
