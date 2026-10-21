export type IconName =
  'star' | 'analyze' | 'nlp' | 'chart' | 'book' | 'arrow' | 'refresh' | 'check' | 'close'

const paths: Record<IconName, string> = {
  star: 'm12 3 2.8 5.7 6.3.9-4.55 4.44 1.07 6.26L12 17.35l-5.62 2.95 1.07-6.26L2.9 9.6l6.3-.9L12 3Z',
  analyze: 'M4 4h16v16H4z M8 8h8 M8 12h5 M8 16h3',
  nlp: 'M5 5h5v5H5z M14 14h5v5h-5z M14 5h5v5h-5z M7.5 10v6.5H14 M10 7.5h4',
  chart: 'M4 3v17h17 M8 15v-4 M13 15V6 M18 15V9',
  book: 'M12 5c-3-2-6-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1Zm0 0v15',
  arrow: 'M4 12h15 M13 6l6 6-6 6',
  refresh: 'M20 7v5h-5 M4 17v-5h5 M6 6a8 8 0 0 1 13 3 M18 18a8 8 0 0 1-13-3',
  check: 'm5 12 4 4L19 6',
  close: 'm6 6 12 12 M18 6 6 18',
}

export function Icon({ name, className = '' }: { name: IconName; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`icon ${className}`}
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  )
}
