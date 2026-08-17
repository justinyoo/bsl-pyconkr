import { DayPicker, type DateRange } from 'react-day-picker'
import { ko } from 'react-day-picker/locale'
import 'react-day-picker/style.css'
import { allowedRange } from '../lib/dateRange'
import { useMediaQuery } from '../hooks/useMediaQuery'

interface DateRangePickerProps {
  range: DateRange | undefined
  onChange: (range: DateRange | undefined) => void
}

interface DatePickerProps {
  mode: 'single'
  date: Date | undefined
  onChange: (date: Date | undefined) => void
}

interface RangePickerProps {
  mode: 'range'
  range: DateRange | undefined
  onChange: (range: DateRange | undefined) => void
}

/**
 * 조회 가능한 범위(직전 달 1일~오늘)만 선택할 수 있는 Date Range Picker.
 * 한국어 locale과 접근 가능한 이름을 사용한다(TRD 9.3). 모바일에서는 한 달,
 * 충분히 넓은 화면에서는 두 달을 보여준다.
 */
export function DatePicker(props: DatePickerProps | RangePickerProps) {
  const bounds = allowedRange()
  const isWide = useMediaQuery('(min-width: 720px)')
  const commonProps = {
    locale: ko,
    startMonth: bounds.start,
    endMonth: bounds.end,
    disabled: [{ before: bounds.start }, { after: bounds.end }],
    numberOfMonths: isWide ? 2 : 1,
    showOutsideDays: true,
  }

  return (
    <div className="date-range-picker">
      {props.mode === 'range' ? (
        <DayPicker
          {...commonProps}
          mode="range"
          selected={props.range}
          onSelect={props.onChange}
          defaultMonth={props.range?.from ?? bounds.end}
          aria-label="급식 조회 날짜 범위 선택"
        />
      ) : (
        <DayPicker
          {...commonProps}
          mode="single"
          selected={props.date}
          onSelect={props.onChange}
          defaultMonth={props.date ?? bounds.end}
          aria-label="급식 평가 날짜 선택"
        />
      )}
    </div>
  )
}

export function DateRangePicker({ range, onChange }: DateRangePickerProps) {
  return <DatePicker mode="range" range={range} onChange={onChange} />
}
