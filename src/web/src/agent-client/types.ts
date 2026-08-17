export interface EvaluationSchool {
  schoolCode: string
  educationOfficeCode: string
  schoolName: string
  educationOfficeName: string
  locationName: string | null
  schoolType: string | null
}

export interface CriterionResult {
  criterion: 'nutrition_balance' | 'healthiness' | 'menu_quality'
  rating: number
  weight: number
  weightedScore: number
  evidence: string[]
  limitations: string[]
  improvements: string[]
}

export interface SchoolScore {
  school: EvaluationSchool
  criteria: CriterionResult[]
  totalScore: number
}

export interface BattleEvaluation {
  date: string
  schoolScores: SchoolScore[]
  unavailableSchools: EvaluationSchool[]
  outcome: 'first' | 'second' | 'tie' | 'incomplete'
  winnerSchoolCode: string | null
  summary: string
  keyReasons: string[]
  improvements: Record<string, string[]>
  warnings: string[]
}

export interface EvaluationRequest {
  schools: [EvaluationSchool, EvaluationSchool]
  date: string
  prompt: string
}

export type EvaluationStep =
  | 'prepare'
  | 'nutrition_balance'
  | 'healthiness'
  | 'menu_quality'
  | 'score'
  | 'final'

export type ProgressHandler = (
  step: EvaluationStep,
  status: 'running' | 'done',
) => void
