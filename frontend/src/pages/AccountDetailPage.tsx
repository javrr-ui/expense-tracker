import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import AccountForm from '../components/AccountForm'
import {
  applyStatementReconcile,
  getAccount,
  getStatementReconcile,
  getStatements,
  parseStatement,
  setAccountBalance,
  setPaymentCoverage,
  updateAccount,
  uploadStatement,
} from '../lib/api'
import { formatDate, formatMoney, formatPercent } from '../lib/format'
import type { AccountPayload } from '../types/account'
import type { ReconcileReport } from '../types/statement'

export default function AccountDetailPage() {
  const { accountId } = useParams()
  const id = Number(accountId)
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [balanceAmount, setBalanceAmount] = useState('')
  const [balanceNote, setBalanceNote] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [statementFile, setStatementFile] = useState<File | null>(null)
  const [statementPassword, setStatementPassword] = useState('')
  const [reconcile, setReconcile] = useState<ReconcileReport | null>(null)

  const { data: account, isLoading, error: loadError } = useQuery({
    queryKey: ['account', id],
    queryFn: () => getAccount(id),
    enabled: Number.isFinite(id),
  })
  const { data: statements = [] } = useQuery({
    queryKey: ['statements', id],
    queryFn: () => getStatements(id),
    enabled: Number.isFinite(id),
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['account', id] })
    queryClient.invalidateQueries({ queryKey: ['accounts'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    queryClient.invalidateQueries({ queryKey: ['statements', id] })
    queryClient.invalidateQueries({ queryKey: ['transactions'] })
  }

  const updateMutation = useMutation({
    mutationFn: (payload: AccountPayload) => updateAccount(id, payload),
    onSuccess: () => {
      invalidate()
      setEditing(false)
      setError(null)
    },
    onError: (err: Error) => setError(err.message),
  })

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!statementFile) throw new Error('Elige un PDF')
      return uploadStatement(id, statementFile, statementPassword || undefined)
    },
    onSuccess: () => {
      invalidate()
      setStatementFile(null)
      setStatementPassword('')
      setError(null)
    },
    onError: (err: Error) => setError(err.message),
  })

  const previewReconcile = useMutation({
    mutationFn: (statementId: number) => getStatementReconcile(statementId),
    onSuccess: (data) => {
      setReconcile(data)
      setError(null)
    },
    onError: (err: Error) => setError(err.message),
  })

  const applyReconcile = useMutation({
    mutationFn: (statementId: number) => applyStatementReconcile(statementId),
    onSuccess: (data) => {
      setReconcile(data)
      invalidate()
      setError(null)
    },
    onError: (err: Error) => setError(err.message),
  })

  const coverageMutation = useMutation({
    mutationFn: ({ dueDate, status }: { dueDate: string; status: string | null }) =>
      setPaymentCoverage(id, dueDate, status),
    onSuccess: invalidate,
    onError: (err: Error) => setError(err.message),
  })

  const parseMutation = useMutation({
    mutationFn: (statementId: number) => parseStatement(statementId, statementPassword || undefined),
    onSuccess: invalidate,
    onError: (err: Error) => setError(err.message),
  })

  const balanceMutation = useMutation({
    mutationFn: () => setAccountBalance(id, Number(balanceAmount), balanceNote),
    onSuccess: () => {
      invalidate()
      setBalanceAmount('')
      setBalanceNote('')
      setError(null)
    },
    onError: (err: Error) => setError(err.message),
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (loadError || !account) {
    return <div className="p-8 text-center text-red-600">No se encontró la cuenta</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/accounts" className="text-sm text-blue-700 hover:underline">
          ← Cuentas
        </Link>
        <div className="mt-2 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">{account.name}</h2>
            <p className="text-sm text-gray-500">
              {account.bank_display_name} · {account.account_type_label}
              {account.last_four ? ` · ${account.last_four}` : ''}
            </p>
          </div>
          <button
            onClick={() => setEditing((value) => !value)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            {editing ? 'Cerrar edición' : 'Editar'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm sm:col-span-1">
          <p className="text-sm text-gray-500">{account.is_liability ? 'Saldo que debes' : 'Saldo disponible'}</p>
          <p className={`mt-2 text-3xl font-semibold ${account.is_liability ? 'text-red-700' : 'text-emerald-700'}`}>
            {formatMoney(account.current_balance, account.currency)}
          </p>
          {account.credit_limit ? (
            <p className="mt-2 text-xs text-gray-500">
              Límite {formatMoney(account.credit_limit)} · {formatPercent(account.utilization)}
            </p>
          ) : null}
          {account.next_due_date ? (
            <p className="mt-1 text-xs text-gray-500">
              Próximo pago {formatDate(account.next_due_date)}
              {account.payment_frequency_label ? ` · ${account.payment_frequency_label}` : ''}
            </p>
          ) : null}
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm sm:col-span-2">
          <h3 className="font-medium text-gray-900 mb-3">Actualizar saldo</h3>
          <form
            className="flex flex-col sm:flex-row gap-3"
            onSubmit={(event) => {
              event.preventDefault()
              if (balanceAmount === '') return
              balanceMutation.mutate()
            }}
          >
            <input
              type="number"
              step="0.01"
              min="0"
              required
              value={balanceAmount}
              onChange={(event) => setBalanceAmount(event.target.value)}
              placeholder={account.is_liability ? '¿Cuánto debes hoy?' : '¿Cuánto tienes hoy?'}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              value={balanceNote}
              onChange={(event) => setBalanceNote(event.target.value)}
              placeholder="Nota (opcional)"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={balanceMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
            >
              {balanceMutation.isPending ? 'Guardando...' : 'Guardar saldo'}
            </button>
          </form>
          <p className="mt-2 text-xs text-gray-500">
            Esto crea un snapshot. Los movimientos posteriores a esta fecha ajustan el saldo.
          </p>
        </div>
      </div>

      {error ? <div className="rounded-lg bg-red-50 text-red-700 px-3 py-2 text-sm">{error}</div> : null}

      {account.scheduled_payments.length > 0 ? (
        <section className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">Pagos programados</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Calendario de la recurrencia. El saldo de arriba es lo que debes hoy; estas fechas son los pagos por hacer.
            </p>
          </div>
          <ul className="divide-y divide-gray-100">
            {account.scheduled_payments.map((payment) => {
              const today = new Date()
              today.setHours(0, 0, 0, 0)
              const due = new Date(`${payment.date}T00:00:00`)
              const covered = payment.coverage === 'minimum_paid' || payment.coverage === 'paid_in_full'
              const overdue = !covered && due < today
              const soon = !covered && !overdue && (due.getTime() - today.getTime()) / 86400000 <= 3
              return (
                <li
                  key={payment.date}
                  className={`px-5 py-3 flex items-center justify-between gap-3 ${
                    covered ? 'bg-emerald-50' : overdue ? 'bg-red-50' : soon ? 'bg-amber-50' : ''
                  }`}
                >
                  <div>
                    <p className="text-sm text-gray-900">{formatDate(payment.date)}</p>
                    {covered && payment.coverage === 'paid_in_full' ? (
                      <p className="text-xs text-emerald-700">Pagado</p>
                    ) : null}
                    {covered && payment.coverage === 'minimum_paid' ? (
                      <p className="text-xs text-emerald-700">Pago mínimo cubierto</p>
                    ) : null}
                    {overdue ? <p className="text-xs text-red-700">Vencido</p> : null}
                    {soon ? <p className="text-xs text-amber-700">Pronto</p> : null}
                  </div>
                  <div className="text-right space-y-1">
                    <p className="text-sm font-semibold">{formatMoney(payment.amount, account.currency)}</p>
                    <select
                      value={payment.coverage ?? ''}
                      disabled={coverageMutation.isPending}
                      onChange={(event) =>
                        coverageMutation.mutate({
                          dueDate: payment.date,
                          status: event.target.value || null,
                        })
                      }
                      className="text-[11px] border border-gray-300 rounded-md bg-white px-1.5 py-0.5"
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

      {editing ? (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <AccountForm
            initial={account}
            submitLabel="Guardar cambios"
            saving={updateMutation.isPending}
            error={error}
            onSubmit={async (payload) => {
              await updateMutation.mutateAsync(payload)
            }}
            onCancel={() => setEditing(false)}
          />
        </div>
      ) : null}

      <section className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
        <div>
          <h3 className="font-semibold text-gray-900">Estado de cuenta (PDF)</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Sube el PDF de Nu (puede ir con contraseña). El saldo al corte se usa como snapshot.
          </p>
        </div>
        <form
          className="flex flex-col sm:flex-row gap-3"
          onSubmit={(event) => {
            event.preventDefault()
            uploadMutation.mutate()
          }}
        >
          <input
            type="file"
            accept="application/pdf,.pdf"
            onChange={(event) => setStatementFile(event.target.files?.[0] ?? null)}
            className="flex-1 text-sm"
          />
          <input
            type="password"
            value={statementPassword}
            onChange={(event) => setStatementPassword(event.target.value)}
            placeholder="Contraseña del PDF (opcional)"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
          />
          <button
            type="submit"
            disabled={uploadMutation.isPending || !statementFile}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            {uploadMutation.isPending ? 'Subiendo...' : 'Subir PDF'}
          </button>
        </form>
        {statements.length === 0 ? (
          <p className="text-sm text-gray-500">Aún no hay estados de cuenta.</p>
        ) : (
          <ul className="divide-y divide-gray-100 border border-gray-100 rounded-lg">
            {statements.map((statement) => (
              <li key={statement.id} className="px-4 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <p className="text-sm text-gray-900">{statement.source_filename || `Estado #${statement.id}`}</p>
                  <p className="text-xs text-gray-500">
                    {statement.status}
                    {statement.period_start && statement.period_end
                      ? ` · ${formatDate(statement.period_start)} – ${formatDate(statement.period_end)}`
                      : ''}
                    {statement.closing_balance != null ? ` · corte ${formatMoney(statement.closing_balance)}` : ''}
                  </p>
                  {statement.error ? <p className="text-xs text-red-600">{statement.error}</p> : null}
                </div>
                <div className="flex gap-3">
                  {statement.status === 'parsed' ? (
                    <button
                      type="button"
                      onClick={() => previewReconcile.mutate(statement.id)}
                      className="text-sm text-blue-700 hover:underline"
                    >
                      Conciliar
                    </button>
                  ) : null}
                  {statement.status === 'needs_password' || statement.status === 'failed' ? (
                    <button
                      type="button"
                      onClick={() => parseMutation.mutate(statement.id)}
                      className="text-sm text-blue-700 hover:underline"
                    >
                      Reintentar
                    </button>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
        {reconcile ? (
          <div className="border border-gray-100 rounded-lg p-4 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <p className="text-sm text-gray-800">
                Estado #{reconcile.statement_id}: {reconcile.matched} coinciden · {reconcile.only_statement}{' '}
                solo en el PDF · {reconcile.only_ledger} solo en correos
              </p>
              <button
                type="button"
                disabled={applyReconcile.isPending || reconcile.matched === 0}
                onClick={() => applyReconcile.mutate(reconcile.statement_id)}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {applyReconcile.isPending ? 'Uniendo...' : 'Unir coincidencias'}
              </button>
            </div>
            <p className="text-xs text-gray-500">
              Se conserva el registro del correo, se le asigna esta cuenta y se borra el duplicado del PDF. Lo que
              solo está en el estado (compras sin aviso) se queda.
            </p>
            <ul className="max-h-64 overflow-y-auto divide-y divide-gray-100 text-xs">
              {reconcile.items.slice(0, 40).map((item, index) => (
                <li key={`${item.status}-${item.statement_tx_id}-${item.ledger_tx_id}-${index}`} className="py-2">
                  <span
                    className={`inline-block w-28 ${
                      item.status === 'matched'
                        ? 'text-emerald-700'
                        : item.status === 'only_statement'
                          ? 'text-amber-700'
                          : 'text-gray-500'
                    }`}
                  >
                    {item.status === 'matched'
                      ? 'Coincide'
                      : item.status === 'only_statement'
                        ? 'Solo PDF'
                        : 'Solo correo'}
                  </span>
                  <span className="text-gray-800">{formatMoney(item.amount)}</span>
                  {item.date ? <span className="text-gray-400"> · {formatDate(item.date)}</span> : null}
                  <div className="text-gray-500 truncate">
                    {item.statement_description || item.ledger_description}
                    {item.status === 'matched' &&
                    item.ledger_description &&
                    item.statement_description !== item.ledger_description
                      ? ` ↔ ${item.ledger_description}`
                      : ''}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      <section className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">Historial de saldos</h3>
        </div>
        {account.snapshots.length === 0 ? (
          <p className="px-5 py-6 text-sm text-gray-500">Sin snapshots.</p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {account.snapshots.map((snapshot) => (
              <li key={snapshot.id} className="px-5 py-3 flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm text-gray-900">{formatDate(snapshot.as_of)}</p>
                  <p className="text-xs text-gray-500">
                    {snapshot.source}
                    {snapshot.note ? ` · ${snapshot.note}` : ''}
                  </p>
                </div>
                <p className="text-sm font-semibold">{formatMoney(snapshot.amount, account.currency)}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
