import type { ReactNode } from 'react'

type PageHeaderProps = {
  title: string
  // Accept markup so each page can supply its own summary and action controls.
  description?: ReactNode
  actions?: ReactNode
}

// Use once per page to keep the main heading and action spacing consistent.
// Optional content is only rendered when supplied, avoiding empty wrapper elements.
export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div className="page-heading">
        <h1>{title}</h1>
        {description && <div className="page-description">{description}</div>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  )
}
