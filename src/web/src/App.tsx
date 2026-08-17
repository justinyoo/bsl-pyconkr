import { useEffect, useState } from 'react'
import type { SchoolSummary } from './api-client/client'
import { isoToLocalDate } from './lib/dateRange'
import { SiteHeader } from './components/SiteHeader'
import { SchoolSearchPage } from './pages/SchoolSearchPage'
import { DateSelectionPage } from './pages/DateSelectionPage'
import { MealResultsPage } from './pages/MealResultsPage'

type Step = 'school' | 'dates' | 'meals'

interface SelectedRange {
  from: string
  to: string
}

function App() {
  const [step, setStep] = useState<Step>('school')
  const [school, setSchool] = useState<SchoolSummary | null>(null)
  const [range, setRange] = useState<SelectedRange | null>(null)

  useEffect(() => {
    if (
      window.location.pathname !== '/' ||
      window.location.search ||
      window.location.hash
    ) {
      window.history.replaceState(null, '', '/')
    }
  }, [])

  function handleSchoolSelect(selectedSchool: SchoolSummary) {
    setSchool(selectedSchool)
    setRange(null)
    setStep('dates')
  }

  function handleDateSelect(selectedRange: SelectedRange) {
    setRange(selectedRange)
    setStep('meals')
  }

  function handleSchoolChange() {
    setSchool(null)
    setRange(null)
    setStep('school')
  }

  function handleDateChange() {
    setStep('dates')
  }

  return (
    <div className="app-shell">
      <SiteHeader />
      <main className="app-main">
        {step === 'school' ? (
          <SchoolSearchPage onSelect={handleSchoolSelect} />
        ) : null}
        {step === 'dates' && school ? (
          <DateSelectionPage
            school={school}
            initialRange={
              range
                ? {
                    from: isoToLocalDate(range.from),
                    to: isoToLocalDate(range.to),
                  }
                : undefined
            }
            onChangeSchool={handleSchoolChange}
            onSubmit={handleDateSelect}
          />
        ) : null}
        {step === 'meals' && school && range ? (
          <MealResultsPage
            school={school}
            from={range.from}
            to={range.to}
            onChangeSchool={handleSchoolChange}
            onChangeDates={handleDateChange}
          />
        ) : null}
      </main>
    </div>
  )
}

export default App
