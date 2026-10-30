import type { ReactNode } from 'react'

type IconName = 'cards' | 'search' | 'sun' | 'moon' | 'grid' | 'list' | 'plus' | 'user' | 'check' | 'logout'

// Store only the shapes here; the shared SVG below sets size and stroke style.
const shapes: Record<IconName, ReactNode> = {
  cards: <><path d="m7 5-3 .8a1.5 1.5 0 0 0-1.1 1.8L5.6 19a1.5 1.5 0 0 0 1.8 1.1L10 19.5" /><rect x="8" y="3" width="12" height="17" rx="2" /></>,
  search: <><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 4.5 4.5" /></>,
  sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4m0-14.2-1.4 1.4M6.3 17.7l-1.4 1.4" /></>,
  moon: <path d="M20.5 13.1A8.5 8.5 0 0 1 10.9 3.5a8.5 8.5 0 1 0 9.6 9.6Z" />,
  grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
  list: <><path d="M8 5h13M8 12h13M8 19h13M3 5h.01M3 12h.01M3 19h.01" /></>,
  plus: <path d="M12 5v14M5 12h14" />,
  user: <><circle cx="12" cy="8" r="3.5" /><path d="M5 21v-2a7 7 0 0 1 14 0v2" /></>,
  check: <path d="m5 12 4 4L19 6" />,
  // The exit arrow follows the same outline style as the navigation icons.
  logout: <><path d="M9 5H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4" /><path d="m16 8 4 4-4 4M20 12H9" /></>,
}

// currentColor follows the surrounding text color in either theme. Icons are
// decorative: the adjacent text supplies the accessible name for each control.
export function Icon({ name, className = '' }: { name: IconName; className?: string }) {
  return (
    <svg className={`icon ${className}`} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.65" strokeLinecap="round"
      strokeLinejoin="round" aria-hidden="true" focusable="false">
      {shapes[name]}
    </svg>
  )
}
