import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getBudgets, getCategories, upsertBudget } from '../lib/api'
import { formatMoney, formatPercent } from '../lib/format'

const MONTHS = [
  'Enero',
  'Febrero',
  'Marzo',
  'Abril',
  'Mayo',
  'Junio',
  'Julio',
  'Agosto',
  'Septiembre',
  'Octubre',
  'Noviembre',
  'Diciembre',
]

export default function BudgetPage() {
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [drafts, setDrafts] = useState<Record<number, string>>({})
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['budgets', year, month],
    queryFn: () => getBudgets(year, month),
  })
  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
  })

  const save = useMutation({
    mutationFn: (payload: { category_id: number; amount: number }) =>
      upsertBudget({ ...payload, year, month }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
    },
  })

  const rows = useMemo(() => {
    const existing = new Map((data?.items ?? []).map((item) => [item.category_id, item]))
    return categories
      .filter((category) => category.kind !== 'income')
      .map((category) => {
        const item = existing.get(category.id)
        return {
          category_id: category.id,
          category_name: category.name,
          color: category.color,
          budget: item?.budget ?? 0,
          spent: item?.spent ?? 0,
          remaining: item?.remaining ?? 0,
          pct: item?.pct ?? null,
        }
      })
  }, [categories, data])

  const totalBudget = rows.reduce((sum, row) => sum + row.budget, 0)
  const totalSpent = data?.total_spent ?? 0

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Presupuesto</h2>
          <p className="text-sm text-gray-500 mt-1">
            Compara lo planeado contra lo gastado. Pagos de deuda y transferencias no entran.
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={month}
            onChange={(event) => setMonth(Number(event.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm"
          >
            {MONTHS.map((label, index) => (
              <option key={label} value={index + 1}>
                {label}
              </option>
            ))}
          </select>
          <input
            type="number"
            value={year}
            onChange={(event) => setYear(Number(event.target.value))}
            className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <p className="text-sm text-gray-500">Presupuesto del mes</p>
          <p className="mt-2 text-2xl font-semibold">{formatMoney(totalBudget)}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <p className="text-sm text-gray-500">Gastado</p>
          <p className="mt-2 text-2xl font-semibold">{formatMoney(totalSpent)}</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : error ? (
        <div className="p-8 text-center text-red-600">No se pudo cargar el presupuesto</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <ul className="divide-y divide-gray-100">
            {rows.map((row) => {
              const pct = row.budget > 0 ? Math.min(1, row.spent / row.budget) : row.spent > 0 ? 1 : 0
              const over = row.budget > 0 && row.spent > row.budget
              return (
                <li key={row.category_id} className="px-5 py-4 space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: row.color }} />
                        <p className="font-medium text-gray-900">{row.category_name}</p>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Gastado {formatMoney(row.spent)}
                        {row.budget > 0 ? ` · queda ${formatMoney(row.remaining)}` : ' · sin presupuesto'}
                        {row.pct != null ? ` · ${formatPercent(row.pct)}` : ''}
                      </p>
                    </div>
                    <label className="text-sm flex items-center gap-2">
                      <span className="text-gray-500">Límite</span>
                      <input
                        type="number"
                        min="0"
                        step="50"
                        value={drafts[row.category_id] ?? String(row.budget || '')}
                        onChange={(event) =>
                          setDrafts((current) => ({ ...current, [row.category_id]: event.target.value }))
                        }
                        onBlur={() => {
                          const raw = drafts[row.category_id]
                          if (raw === undefined) return
                          const amount = Number(raw)
                          if (Number.isNaN(amount) || amount < 0) return
                          if (amount === row.budget) return
                          save.mutate({ category_id: row.category_id, amount })
                        }}
                        className="w-28 px-3 py-1.5 border border-gray-300 rounded-lg"
                      />
                    </label>
                  </div>
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${over ? 'bg-red-500' : 'bg-blue-500'}`}
                      style={{ width: `${pct * 100}%` }}
                    />
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
