// ===========================
// utils.ts
// ©AngelaMos | 2025
// ===========================

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins.toString()}m ago`
  if (diffHours < 24) return `${diffHours.toString()}h ago`
  if (diffDays < 7) return `${diffDays.toString()}d ago`

  return formatDate(dateString)
}

export const formatDuration = (durationMs: number | null): string => {
  if (durationMs === null) return '—'
  if (durationMs < 1000) return `${durationMs.toString()} ms`

  return `${(durationMs / 1000).toFixed(1)} s`
}
