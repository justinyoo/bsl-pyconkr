export type AppView = 'lookup' | 'analysis'

interface SiteHeaderProps {
  activeView: AppView
  onNavigate: (view: AppView) => void
}

export function SiteHeader({ activeView, onNavigate }: SiteHeaderProps) {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <div className="site-header__brand">
          <span className="site-header__mark" aria-hidden="true">
            🍱
          </span>
          <div>
            <p className="site-header__title">급식 배틀</p>
            <p className="site-header__subtitle">우리 학교 오늘 뭐 먹지?</p>
          </div>
        </div>
        <nav className="site-nav" aria-label="주요 메뉴">
          <button
            type="button"
            className={activeView === 'lookup' ? 'is-active' : ''}
            aria-current={activeView === 'lookup' ? 'page' : undefined}
            onClick={() => onNavigate('lookup')}
          >
            정보 조회
          </button>
          <button
            type="button"
            className={activeView === 'analysis' ? 'is-active' : ''}
            aria-current={activeView === 'analysis' ? 'page' : undefined}
            onClick={() => onNavigate('analysis')}
          >
            급식 분석
          </button>
        </nav>
      </div>
    </header>
  )
}
