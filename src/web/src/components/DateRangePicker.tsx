import { DayPicker, type DateRange } from 'react-day-picker'
import { ko } from 'react-day-picker/locale'
import 'react-day-picker/style.css'
import { allowedRange } from '../lib/dateRange'
import { useMediaQuery } from '../hooks/useMediaQuery'

interface DateRangePickerProps {
  range: DateRange | undefined
  onChange: (range: DateRange | undefined) => void
}

/**
 * 조회 가능한 범위(직전 달 1일~오늘)만 선택할 수 있는 Date Range Picker.
 * 한국어 locale과 접근 가능한 이름을 사용한다(TRD 9.3). 모바일에서는 한 달,
 * 충분히 넓은 화면에서는 두 달을 보여준다.
 */
export function DateRangePicker({ range, onChange }: DateRangePickerProps) {
  const bounds = allowedRange()
  const isWide = useMediaQuery('(min-width: 720px)')

  return (
    <div className="date-range-picker">
      <DayPicker
        mode="range"
        locale={ko}
        selected={range}
        onSelect={onChange}
        startMonth={bounds.start}
        endMonth={bounds.end}
        hidden={[{ before: bounds.start }, { after: bounds.end }]}
        numberOfMonths={isWide ? 2 : 1}
        defaultMonth={range?.from ?? bounds.end}
        showOutsideDays
        aria-label="급식 조회 날짜 범위 선택"
      />
    </div>
  )
}

