export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="site-header__brand">
        <span className="site-header__mark" aria-hidden="true">
          🍱
        </span>
        <div>
          <p className="site-header__title">급식 배틀</p>
          <p className="site-header__subtitle">우리 학교 오늘 뭐 먹지?</p>
        </div>
      </div>
    </header>
  )
}
