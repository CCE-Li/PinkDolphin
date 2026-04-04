export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '--'
  return new Date(value).toLocaleString()
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return '--'
  return value.toLocaleString()
}

export function truncate(value: string | null | undefined, length = 120): string {
  if (!value) return '--'
  if (value.length <= length) return value
  return `${value.slice(0, length)}...`
}
