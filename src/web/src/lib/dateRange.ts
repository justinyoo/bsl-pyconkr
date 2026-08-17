/**
 * 한국 표준시(KST) 기준 날짜 범위 계산과 검증.
 *
 * 백엔드(`bsl_api.services.dates`)와 동일한 규칙을 프론트엔드에서도
 * 적용해 사용자가 조회 전에 오류를 확인할 수 있도록 한다. 최종 검증은
 * 백엔드가 다시 수행하지만, 여기서는 실제 네트워크 요청을 보내기 전에
 * 동일한 규칙으로 먼저 걸러낸다.
 */

const KST_TIME_ZONE = 'Asia/Seoul'

/** 달력 날짜(연/월/일)만 표현한다. 시간대는 항상 KST 기준이다. */
export interface CalendarDate {
  year: number
  month: number // 1-12
  day: number
}

function toCalendarDate(date: Date): CalendarDate {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: KST_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
  const parts = formatter.formatToParts(date)
  const get = (type: string) =>
    Number(parts.find((part) => part.type === type)?.value)
  return { year: get('year'), month: get('month'), day: get('day') }
}

/** 실행 시점의 KST 기준 "오늘" 달력 날짜를 반환한다. */
export function todayKst(): CalendarDate {
  return toCalendarDate(new Date())
}

function calendarDateToLocalDate(calendarDate: CalendarDate): Date {
  return new Date(calendarDate.year, calendarDate.month - 1, calendarDate.day)
}

function localDateToCalendarDate(date: Date): CalendarDate {
  return { year: date.getFullYear(), month: date.getMonth() + 1, day: date.getDate() }
}

/** react-day-picker 등에서 사용할 수 있도록 KST 오늘을 로컬 자정 Date로 변환한다. */
export function todayAsLocalDate(): Date {
  return calendarDateToLocalDate(todayKst())
}

export function isoToLocalDate(iso: string): Date {
  const [year, month, day] = iso.split('-').map(Number)
  return new Date(year, month - 1, day)
}

export function localDateToIso(date: Date): string {
  const { year, month, day } = localDateToCalendarDate(date)
  return `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

function firstDayOfPreviousMonth(reference: CalendarDate): CalendarDate {
  if (reference.month === 1) {
    return { year: reference.year - 1, month: 12, day: 1 }
  }
  return { year: reference.year, month: reference.month - 1, day: 1 }
}

export interface AllowedRange {
  start: Date
  end: Date
}

/** 조회 가능한 날짜 범위: 직전 달 1일부터 오늘까지(KST 기준). */
export function allowedRange(reference: CalendarDate = todayKst()): AllowedRange {
  return {
    start: calendarDateToLocalDate(firstDayOfPreviousMonth(reference)),
    end: calendarDateToLocalDate(reference),
  }
}

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

/** 기본 날짜 범위: 오늘로부터 7일 전부터 오늘까지, 허용 범위로 잘라낸다(clamp). */
export function defaultRange(reference: CalendarDate = todayKst()): AllowedRange {
  const bounds = allowedRange(reference)
  const today = calendarDateToLocalDate(reference)
  const sevenDaysAgo = new Date(today)
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
  const start = sevenDaysAgo < bounds.start ? bounds.start : sevenDaysAgo
  return { start, end: bounds.end }
}

export type DateRangeErrorCode = 'REVERSED' | 'BEFORE_START' | 'AFTER_END'

export interface DateRangeValidationResult {
  valid: boolean
  errorCode?: DateRangeErrorCode
  message?: string
}

/**
 * 날짜 범위가 역순이거나 허용 범위를 벗어나면 사람이 읽을 수 있는 오류를
 * 반환한다. 통과하면 `valid: true`.
 */
export function validateDateRange(
  from: Date | undefined,
  to: Date | undefined,
  reference: CalendarDate = todayKst(),
): DateRangeValidationResult {
  if (!from || !to) {
    return {
      valid: false,
      errorCode: 'REVERSED',
      message: '시작일과 종료일을 모두 선택해 주세요.',
    }
  }

  const bounds = allowedRange(reference)
  const fromDay = startOfDay(from)
  const toDay = startOfDay(to)

  if (fromDay.getTime() > toDay.getTime()) {
    return {
      valid: false,
      errorCode: 'REVERSED',
      message: '종료일은 시작일보다 빠를 수 없습니다.',
    }
  }
  if (fromDay.getTime() < bounds.start.getTime()) {
    return {
      valid: false,
      errorCode: 'BEFORE_START',
      message: '조회 가능한 시작일은 직전 달 1일부터입니다.',
    }
  }
  if (toDay.getTime() > bounds.end.getTime()) {
    return {
      valid: false,
      errorCode: 'AFTER_END',
      message: '조회 가능한 종료일은 오늘까지입니다.',
    }
  }

  return { valid: true }
}
