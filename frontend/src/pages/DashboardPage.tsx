import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CreditCard, Landmark, Wallet } from 'lucide-react'
import { getBudgets, getDashboard, setPaymentCoverage } from '../lib/api'
import { formatDate, formatMoney, formatPercent } from '../lib/format'
import type { Account, UpcomingPayment } from '../types/account'
import SpendingCharts from '../components/SpendingCharts'

function SummaryCard({
  label,
  value,
  hint,
  tone,
}: {
  label: string
  value: string
  hint?: string
  tone: 'debt' | 'asset' | 'net'
}) {
  const tones = {
    debt: 'text-red-700',
    asset: 'text-emerald-700',
    net: 'text-gray-900',
  }
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`mt-2 text-2xl sm:text-3xl font-semibold ${tones[tone]}`}>{value}</p>
      {hint ? <p className="mt-1 text-xs text-gray-400">{hint}</p> : null}
    </div>
  )
}

function AccountCard({ account }: { account: Account }) {
  const Icon = account.is_liability ? CreditCard : account.account_type === 'wallet' ? Wallet : Landmark
  return (
    <Link
      to={`/accounts/${account.id}`}
      className="block bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:border-blue-300 hover:shadow transition-all"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
            <Icon className="w-5 h-5 text-gray-600" />
          </div>
          <div className="min-w-0">
            <p className="font-medium text-gray-900 truncate">{account.name}</p>
            <p className="text-sm text-gray-500">
              {account.bank_display_name}
              {account.last_four ? ` · ${account.last_four}` : ''}
            </p>
          </div>
        </div>
        <p className={`text-lg font-semibold ${account.is_liability ? 'text-red-700' : 'text-emerald-700'}`}>
          {formatMoney(account.current_balance, account.currency)}
        </p>
      </div>
      {account.credit_limit ? (
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Utilización {formatPercent(account.utilization)}</span>
            <span>Límite {formatMoney(account.credit_limit, account.currency)}</span>
          </div>
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                (account.utilization ?? 0) > 0.7 ? 'bg-red-500' : 'bg-blue-500'
              }`}
              style={{ width: `${Math.min(100, (account.utilization ?? 0) * 100)}%` }}
            />
          </div>
        </div>
      ) : null}
      {account.next_due_date ? (
        <p className="mt-3 text-xs text-gray-500">
          Próximo pago {formatDate(account.next_due_date)}
          {account.payment_frequency_label ? ` · ${account.payment_frequency_label}` : ''}
        </p>
      ) : null}
    </Link>
  )
}

function paymentTone(status: UpcomingPayment['status']) {
  if (status === 'minimum_paid' || status === 'paid_in_full') return 'bg-emerald-50'
  if (status === 'overdue') return 'bg-red-50'
  if (status === 'due_soon') return 'bg-amber-50'
  return ''
}

function paymentBadge(status: UpcomingPayment['status']) {
  if (status === 'paid_in_full') return { label: 'Pagado', className: 'bg-emerald-100 text-emerald-800' }
  if (status === 'minimum_paid') return { label: 'Pago mín. cubierto', className: 'bg-emerald-100 text-emerald-800' }
  if (status === 'overdue') return { label: 'Vencido', className: 'bg-red-100 text-red-800' }
  if (status === 'due_soon') return { label: 'Pronto', className: 'bg-amber-100 text-amber-800' }
  return { label: 'Programado', className: 'bg-gray-100 text-gray-600' }
}

export default function DashboardPage() {
  const now = new Date()
  const queryClient = useQueryClient()
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
  })
  const cover = useMutation({
    mutationFn: ({ accountId, dueDate, status }: { accountId: number; dueDate: string; status: string | null }) =>
      setPaymentCoverage(accountId, dueDate, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['account'] })
    },
  })
  const { data: budgets } = useQuery({
    queryKey: ['budgets', now.getFullYear(), now.getMonth() + 1],
    queryFn: () => getBudgets(now.getFullYear(), now.getMonth() + 1),
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (error || !data) {
    return <div className="p-8 text-center text-red-600">No se pudo cargar el dashboard</div>
  }

  const empty = data.liability_accounts.length === 0 && data.asset_accounts.length === 0

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-gray-900">Resumen</h2>
        <p className="text-sm text-gray-500 mt-1">Dinero en cuentas y deudas, con saldos que tú controlas.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SummaryCard label="Deuda total" value={formatMoney(data.total_debt)} tone="debt" />
        <SummaryCard label="Dinero en cuentas" value={formatMoney(data.total_assets)} tone="asset" />
        <SummaryCard
          label="Posición neta"
          value={formatMoney(data.net_position)}
          hint="Dinero menos deuda. No incluye inversiones."
          tone="net"
        />
      </div>

      <SpendingCharts />

      {budgets && budgets.items.length > 0 ? (
        <section className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Presupuesto del mes</h3>
            <Link to="/budgets" className="text-sm text-blue-700 hover:underline">
              Ver todo
            </Link>
          </div>
          <ul className="divide-y divide-gray-100">
            {budgets.items
              .filter((item) => item.budget > 0)
              .slice(0, 5)
              .map((item) => {
                const pct = item.budget > 0 ? Math.min(1, item.spent / item.budget) : 0
                return (
                  <li key={item.category_id} className="px-5 py-3">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-800">{item.category_name}</span>
                      <span className="text-gray-500">
                        {formatMoney(item.spent)} / {formatMoney(item.budget)}
                      </span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${item.spent > item.budget ? 'bg-red-500' : 'bg-blue-500'}`}
                        style={{ width: `${pct * 100}%` }}
                      />
                    </div>
                  </li>
                )
              })}
          </ul>
        </section>
      ) : null}

      {empty ? (
        <div className="bg-white border border-dashed border-gray-300 rounded-xl p-8 text-center">
          <p className="text-gray-700 font-medium">Todavía no hay cuentas</p>
          <p className="text-sm text-gray-500 mt-1">Crea tus tarjetas, préstamos y cheques para ver el resumen.</p>
          <Link
            to="/accounts"
            className="inline-flex mt-4 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
          >
            Ir a cuentas
          </Link>
        </div>
      ) : null}

      {data.liability_accounts.length > 0 ? (
        <section className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">Deudas</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.liability_accounts.map((account) => (
              <AccountCard key={account.id} account={account} />
            ))}
          </div>
        </section>
      ) : null}

      {data.asset_accounts.length > 0 ? (
        <section className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">Dinero disponible</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.asset_accounts.map((account) => (
              <AccountCard key={account.id} account={account} />
            ))}
          </div>
        </section>
      ) : null}

      {data.upcoming_payments.length > 0 ? (
        <section className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">Próximos pagos</h3>
          </div>
          <ul className="divide-y divide-gray-100">
            {data.upcoming_payments.map((payment) => {
              const badge = paymentBadge(payment.status)
              return (
                <li
                  key={`${payment.account_id}-${payment.due_date}`}
                  className={`px-5 py-3 flex items-center justify-between gap-3 ${paymentTone(payment.status)}`}
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{payment.account_name}</p>
                    <p className="text-xs text-gray-500">
                      {payment.bank_display_name} · {formatDate(payment.due_date)}
                    </p>
                  </div>
                  <div className="text-right space-y-1">
                    <p className="text-sm font-semibold text-gray-900">{formatMoney(payment.amount)}</p>
                    <span className={`inline-flex px-2 py-0.5 text-[10px] font-medium rounded-full ${badge.className}`}>
                      {badge.label}
                    </span>
                    <select
                      value={
                        payment.status === 'minimum_paid' || payment.status === 'paid_in_full' ? payment.status : ''
                      }
                      disabled={cover.isPending}
                      onChange={(event) =>
                        cover.mutate({
                          accountId: payment.account_id,
                          dueDate: payment.due_date,
                          status: event.target.value || null,
                        })
                      }
                      className="block ml-auto mt-1 text-[11px] border border-gray-300 rounded-md bg-white px-1.5 py-0.5"
                    >
                      <option value="">Pendiente</option>
                      <option value="minimum_paid">Pago mínimo cubierto</option>
                      <option value="paid_in_full">Pagado</option>
                    </select>
                  </div>
                </li>
              )
            })}
          </ul>
        </section>
      ) : null}
    </div>
  )
}
