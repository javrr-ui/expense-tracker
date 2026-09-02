export const KIND_OPTIONS = [
  { value: 'purchase', label: 'Compra' },
  { value: 'payment', label: 'Pago de deuda' },
  { value: 'transfer', label: 'Transferencia' },
  { value: 'income', label: 'Ingreso' },
  { value: 'fee', label: 'Comisión' },
]

export function kindLabel(kind: string | null | undefined): string {
  if (!kind) return '—'
  return KIND_OPTIONS.find((option) => option.value === kind)?.label ?? kind
}
