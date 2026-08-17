import type { ReactNode } from 'react'

interface StatusPanelProps {
  tone: 'error' | 'empty' | 'loading'
  title: string
  description?: string
  children?: ReactNode
}

/**
 * 오류·빈 상태·로딩 상태를 통일된 Bento 카드 형태로 보여준다.
 * `role="status"`/`role="alert"`로 스크린 리더에도 상태 변화가 전달된다.
 */
export function StatusPanel({
  tone,
  title,
  description,
  children,
}: StatusPanelProps) {
  const role = tone === 'error' ? 'alert' : 'status'
  return (
    <div
      className={`bento-card status-panel status-panel--${tone}`}
      role={role}
      aria-live={tone === 'error' ? 'assertive' : 'polite'}
    >
      <p className="status-panel__title">{title}</p>
      {description ? (
        <p className="status-panel__description">{description}</p>
      ) : null}
      {children}
    </div>
  )
}
