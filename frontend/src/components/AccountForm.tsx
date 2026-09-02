import { useEffect, useMemo, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getAccountTypes, getBanks } from '../lib/api'
import type { Account, AccountPayload } from '../types/account'

interface AccountFormProps {
  initial?: Account
  submitLabel: string
  onSubmit: (payload: AccountPayload) => Promise<void>
  onCancel: () => void
  includeOpeningBalance?: boolean
  saving?: boolean
  error?: string | null
}

const empty = {
  name: '',
  bank_name: 'nubank',
  account_type: 'credit_card',
  last_four: '',
  credit_limit: '',
  current_balance: '',
  apr: '',
  minimum_payment: '',
  due_date_day: '',
  cutoff_date_day: '',
  payment_frequency: '',
  recurrence_anchor: '',
  recurrence_end: '',
  remaining_payments: '',
  statement_password: '',
}

export default function AccountForm({
  initial,
  submitLabel,
  onSubmit,
  onCancel,
  includeOpeningBalance = false,
  saving = false,
  error = null,
}: AccountFormProps) {
  const [form, setForm] = useState(empty)

  const { data: types = [] } = useQuery({
    queryKey: ['account-types'],
    queryFn: getAccountTypes,
  })
  const { data: banks = [] } = useQuery({
    queryKey: ['banks'],
    queryFn: getBanks,
  })

  useEffect(() => {
    if (!initial) return
    setForm({
      name: initial.name,
      bank_name: initial.bank_name,
      account_type: initial.account_type,
      last_four: initial.last_four ?? '',
      credit_limit: initial.credit_limit?.toString() ?? '',
      current_balance: '',
      apr: initial.apr ? String(initial.apr) : '',
      minimum_payment: initial.minimum_payment?.toString() ?? '',
      due_date_day: initial.due_date_day?.toString() ?? '',
      cutoff_date_day: initial.cutoff_date_day?.toString() ?? '',
      payment_frequency: initial.payment_frequency ?? '',
      recurrence_anchor: initial.recurrence_anchor ?? '',
      recurrence_end: initial.recurrence_end ?? '',
      remaining_payments: initial.remaining_payments?.toString() ?? '',
      statement_password: '',
    })
  }, [initial])

  const selectedType = useMemo(
    () => types.find((item) => item.name === form.account_type),
    [types, form.account_type]
  )
  const isLiability =
    selectedType?.is_liability ??
    (form.account_type === 'credit_card' || form.account_type === 'loan')

  const set = (key: keyof typeof empty) => (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm((current) => ({ ...current, [key]: event.target.value }))
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const payload: AccountPayload = {
      name: form.name.trim(),
      bank_name: form.bank_name,
      account_type: form.account_type,
      last_four: form.last_four.trim() || null,
      credit_limit: form.credit_limit === '' ? null : Number(form.credit_limit),
      apr: form.apr === '' ? 0 : Number(form.apr),
      minimum_payment: form.minimum_payment === '' ? null : Number(form.minimum_payment),
      due_date_day: form.due_date_day === '' ? null : Number(form.due_date_day),
      cutoff_date_day: form.cutoff_date_day === '' ? null : Number(form.cutoff_date_day),
      payment_frequency: form.payment_frequency || null,
      recurrence_anchor: form.recurrence_anchor || null,
      recurrence_end: form.recurrence_end || null,
      remaining_payments: form.remaining_payments === '' ? null : Number(form.remaining_payments),
    }
    if (includeOpeningBalance) {
      payload.current_balance = form.current_balance === '' ? 0 : Number(form.current_balance)
    }
    if (form.statement_password.trim()) {
      payload.statement_password = form.statement_password
    }
    await onSubmit(payload)
  }

  const inputClass =
    'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error ? (
        <div className="rounded-lg bg-red-50 text-red-700 px-3 py-2 text-sm">{error}</div>
      ) : null}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <label className="block text-sm">
          <span className="font-medium text-gray-700">Nombre</span>
          <input className={`${inputClass} mt-1`} value={form.name} onChange={set('name')} required />
        </label>
        <label className="block text-sm">
          <span className="font-medium text-gray-700">Banco</span>
          <select className={`${inputClass} mt-1`} value={form.bank_name} onChange={set('bank_name')}>
            {banks.map((bank) => (
              <option key={bank.name} value={bank.name}>
                {bank.display_name}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="font-medium text-gray-700">Tipo</span>
          <select className={`${inputClass} mt-1`} value={form.account_type} onChange={set('account_type')}>
            {types.map((type) => (
              <option key={type.name} value={type.name}>
                {type.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="font-medium text-gray-700">Últimos 4 dígitos</span>
          <input
            className={`${inputClass} mt-1`}
            value={form.last_four}
            onChange={set('last_four')}
            maxLength={4}
            inputMode="numeric"
            placeholder="4412"
          />
        </label>
        {includeOpeningBalance ? (
          <label className="block text-sm">
            <span className="font-medium text-gray-700">
              {isLiability ? 'Saldo que debes hoy' : 'Saldo disponible hoy'}
            </span>
            <input
              className={`${inputClass} mt-1`}
              value={form.current_balance}
              onChange={set('current_balance')}
              type="number"
              min="0"
              step="0.01"
            />
          </label>
        ) : null}
        {isLiability ? (
          <label className="block text-sm">
            <span className="font-medium text-gray-700">Límite de crédito</span>
            <input
              className={`${inputClass} mt-1`}
              value={form.credit_limit}
              onChange={set('credit_limit')}
              type="number"
              min="0"
              step="0.01"
            />
          </label>
        ) : null}
        {isLiability ? (
          <label className="block text-sm">
            <span className="font-medium text-gray-700">APR %</span>
            <input className={`${inputClass} mt-1`} value={form.apr} onChange={set('apr')} type="number" min="0" step="0.01" />
          </label>
        ) : null}
        {isLiability ? (
          <label className="block text-sm">
            <span className="font-medium text-gray-700">
              {form.account_type === 'loan' ? 'Monto de cada pago' : 'Pago mínimo'}
            </span>
            <input
              className={`${inputClass} mt-1`}
              value={form.minimum_payment}
              onChange={set('minimum_payment')}
              type="number"
              min="0"
              step="0.01"
            />
          </label>
        ) : null}
        {isLiability ? (
          <label className="block text-sm">
            <span className="font-medium text-gray-700">Recurrencia de pago</span>
            <select
              className={`${inputClass} mt-1`}
              value={form.payment_frequency}
              onChange={set('payment_frequency')}
            >
              <option value="">Sin recurrencia</option>
              <option value="weekly">Cada semana</option>
              <option value="biweekly">Cada 2 semanas</option>
              <option value="monthly">Cada mes</option>
            </select>
          </label>
        ) : null}
        {isLiability && form.payment_frequency ? (
          <label className="block text-sm">
            <span className="font-medium text-gray-700">Próximo pago / fecha ancla</span>
            <input
              className={`${inputClass} mt-1`}
              value={form.recurrence_anchor}
              onChange={set('recurrence_anchor')}
              type="date"
              required={form.payment_frequency === 'weekly' || form.payment_frequency === 'biweekly'}
            />
          </label>
        ) : null}
        {isLiability && form.payment_frequency ? (
          <label className="block text-sm">
            <span className="font-medium text-gray-700">Pagos restantes (opcional)</span>
            <input
              className={`${inputClass} mt-1`}
              value={form.remaining_payments}
              onChange={set('remaining_payments')}
              type="number"
              min="1"
              placeholder="Ej. 12"
            />
          </label>
        ) : null}
        {isLiability && form.payment_frequency ? (
          <label className="block text-sm">
            <span className="font-medium text-gray-700">Último pago (opcional)</span>
            <input
              className={`${inputClass} mt-1`}
              value={form.recurrence_end}
              onChange={set('recurrence_end')}
              type="date"
            />
          </label>
        ) : null}
        {isLiability && (!form.payment_frequency || form.payment_frequency === 'monthly') ? (
          <label className="block text-sm">
            <span className="font-medium text-gray-700">Día de pago</span>
            <input
              className={`${inputClass} mt-1`}
              value={form.due_date_day}
              onChange={set('due_date_day')}
              type="number"
              min="1"
              max="31"
            />
          </label>
        ) : null}
        {isLiability && form.account_type === 'credit_card' ? (
          <label className="block text-sm">
            <span className="font-medium text-gray-700">Día de corte</span>
            <input
              className={`${inputClass} mt-1`}
              value={form.cutoff_date_day}
              onChange={set('cutoff_date_day')}
              type="number"
              min="1"
              max="31"
            />
          </label>
        ) : null}
        <label className="block text-sm sm:col-span-2">
          <span className="font-medium text-gray-700">Contraseña del estado de cuenta (opcional)</span>
          <input
            className={`${inputClass} mt-1`}
            value={form.statement_password}
            onChange={set('statement_password')}
            type="password"
            autoComplete="off"
            placeholder={initial?.has_statement_password ? 'Dejar vacío para no cambiar' : ''}
          />
        </label>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Guardando...' : submitLabel}
        </button>
      </div>
    </form>
  )
}
