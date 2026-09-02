import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { endOfDay, formatISO, startOfMonth, startOfYear, subMonths } from 'date-fns'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { getCategoryStats } from '../lib/api'
import { formatMoney, formatPercent } from '../lib/format'

type Period = 'month' | 'quarter' | 'year' | 'all'

function periodRange(period: Period): { from?: string; to?: string } {
  const now = new Date()
  const to = formatISO(endOfDay(now), { representation: 'date' })
  if (period === 'month') {
    return { from: formatISO(startOfMonth(now), { representation: 'date' }), to }
  }
  if (period === 'quarter') {
    return { from: formatISO(subMonths(now, 3), { representation: 'date' }), to }
  }
  if (period === 'year') {
    return { from: formatISO(startOfYear(now), { representation: 'date' }), to }
  }
  return {}
}

export default function SpendingCharts() {
  const [period, setPeriod] = useState<Period>('month')
  const [selected, setSelected] = useState<string | null>(null)
  const range = useMemo(() => periodRange(period), [period])

  const { data, isLoading } = useQuery({
    queryKey: ['category-stats', period],
    queryFn: () => getCategoryStats(range.from, range.to, 'expense'),
  })

  const chartData = data?.categories ?? []
  const active = chartData.find((item) => item.category_name === selected) ?? chartData[0]

  return (
    <section className="bg-white border border-gray-200 rounded-xl shadow-sm p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">En qué se va el dinero</h3>
          <p className="text-sm text-gray-500">Gastos por categoría. Click en una rebanada para ver subcategorías.</p>
        </div>
        <select
          value={period}
          onChange={(event) => {
            setPeriod(event.target.value as Period)
            setSelected(null)
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
        >
          <option value="month">Este mes</option>
          <option value="quarter">Últimos 3 meses</option>
          <option value="year">Este año</option>
          <option value="all">Todo</option>
        </select>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : !data || data.total === 0 ? (
        <p className="text-sm text-gray-500 py-6 text-center">No hay gastos en este periodo.</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey="amount"
                  nameKey="category_name"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={2}
                  onClick={(_, index) => setSelected(chartData[index]?.category_name ?? null)}
                >
                  {chartData.map((item) => (
                    <Cell key={item.category_name} fill={item.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => formatMoney(Number(value ?? 0))}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div>
            <p className="text-sm text-gray-500">Total</p>
            <p className="text-2xl font-semibold text-gray-900">{formatMoney(data.total)}</p>
            {data.uncategorized > 0 ? (
              <p className="text-sm text-amber-700 mt-1">
                Sin categoría: {formatMoney(data.uncategorized)} ({formatPercent(data.uncategorized / data.total)})
              </p>
            ) : null}
            <ul className="mt-4 space-y-2 max-h-48 overflow-y-auto">
              {chartData.map((item) => (
                <li key={item.category_name}>
                  <button
                    type="button"
                    onClick={() => setSelected(item.category_name)}
                    className={`w-full flex items-center justify-between text-sm px-2 py-1 rounded ${
                      active?.category_name === item.category_name ? 'bg-gray-50' : ''
                    }`}
                  >
                    <span className="flex items-center gap-2 min-w-0">
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: item.color }} />
                      <span className="truncate">{item.category_name}</span>
                    </span>
                    <span className="font-medium">{formatMoney(item.amount)}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
          {active ? (
            <div className="lg:col-span-2 border-t border-gray-100 pt-4">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">
                {active.category_name} · subcategorías
              </h4>
              <div className="space-y-2">
                {active.subcategories.map((sub) => (
                  <div key={sub.subcategory_name} className="flex items-center gap-3 text-sm">
                    <span className="w-40 truncate text-gray-600">{sub.subcategory_name}</span>
                    <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${Math.min(100, (sub.amount / active.amount) * 100)}%`,
                          background: active.color,
                        }}
                      />
                    </div>
                    <span className="w-24 text-right font-medium">{formatMoney(sub.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </section>
  )
}
