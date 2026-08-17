const KST_DATE = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Seoul',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
})

const toIsoDate = (year: number, month: number, day: number) =>
  `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`

export function getEvaluationDateBounds(
  now = new Date(),
): { min: string; max: string } {
  const parts = Object.fromEntries(
    KST_DATE.formatToParts(now).map((part) => [part.type, part.value]),
  )
  const year = Number(parts.year)
  const month = Number(parts.month)
  const day = Number(parts.day)
  const previousMonth = new Date(Date.UTC(year, month - 2, 1))
  return {
    min: toIsoDate(
      previousMonth.getUTCFullYear(),
      previousMonth.getUTCMonth() + 1,
      1,
    ),
    max: toIsoDate(year, month, day),
  }
}
