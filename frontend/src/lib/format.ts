export function formatMoney(amount: number, currency = 'MXN'): string {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency,
  }).format(amount)
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const date = dateStr.length <= 10 ? new Date(`${dateStr}T00:00:00`) : new Date(dateStr)
  if (Number.isNaN(date.getTime())) return dateStr
  return new Intl.DateTimeFormat('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

export function formatPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) return '—'
  return `${Math.round(value * 100)}%`
}
