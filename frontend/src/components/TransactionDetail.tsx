import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { deleteTransaction, getAccounts, updateTransaction } from '../lib/api'
import { formatMoney } from '../lib/format'
import { KIND_OPTIONS } from '../lib/kinds'
import type { Transaction } from '../types/transaction'

interface TransactionDetailProps {
  transaction: Transaction
  onClose: () => void
}

export default function TransactionDetail({ transaction, onClose }: TransactionDetailProps) {
  const queryClient = useQueryClient()
  const [notes, setNotes] = useState(transaction.notes ?? '')
  const [tagsText, setTagsText] = useState((transaction.tags ?? []).join(', '))
  const [kind, setKind] = useState(transaction.kind ?? '')
  const [accountId, setAccountId] = useState<number | ''>(transaction.account_id ?? '')
  const [excluded, setExcluded] = useState(Boolean(transaction.excluded_from_budget))
  const [reimbursable, setReimbursable] = useState(Boolean(transaction.reimbursable))

  const { data: accounts = [] } = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
  })

  useEffect(() => {
    setNotes(transaction.notes ?? '')
    setTagsText((transaction.tags ?? []).join(', '))
    setKind(transaction.kind ?? '')
    setAccountId(transaction.account_id ?? '')
    setExcluded(Boolean(transaction.excluded_from_budget))
    setReimbursable(Boolean(transaction.reimbursable))
  }, [transaction])

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['transactions'] })
    queryClient.invalidateQueries({ queryKey: ['category-stats'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    queryClient.invalidateQueries({ queryKey: ['accounts'] })
    queryClient.invalidateQueries({ queryKey: ['budgets'] })
  }

  const save = useMutation({
    mutationFn: () =>
      updateTransaction(transaction.transaction_id, {
        notes: notes.trim() || null,
        tags: tagsText
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
        kind: kind || null,
        account_id: accountId === '' ? null : Number(accountId),
        excluded_from_budget: excluded,
        reimbursable,
      }),
    onSuccess: invalidate,
  })

  const remove = useMutation({
    mutationFn: () => deleteTransaction(transaction.transaction_id),
    onSuccess: () => {
      invalidate()
      onClose()
    },
  })

  return (
    <aside className="fixed inset-y-0 right-0 w-full max-w-md bg-white border-l border-gray-200 shadow-xl z-20 overflow-y-auto">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">Detalle</h3>
        <button type="button" onClick={onClose} className="p-1 text-gray-500 hover:text-gray-800">
          <X className="w-5 h-5" />
        </button>
      </div>
      <div className="p-5 space-y-4 text-sm">
        <div>
          <p className="text-gray-500">Monto</p>
          <p className="text-xl font-semibold">{formatMoney(transaction.amount, transaction.currency || 'MXN')}</p>
          {transaction.currency && transaction.currency !== 'MXN' && transaction.amount_mxn ? (
            <p className="text-xs text-gray-500">≈ {formatMoney(transaction.amount_mxn, 'MXN')}</p>
          ) : null}
        </div>
        <p className="text-gray-800">{transaction.description || '—'}</p>
        <p className="text-gray-500">
          {transaction.bank_name}
          {transaction.account_name ? ` · ${transaction.account_name}` : ''}
          {transaction.merchant ? ` · ${transaction.merchant}` : ''}
        </p>
        {transaction.source ? (
          <p className="text-xs text-gray-400">Origen: {transaction.source}</p>
        ) : null}

        <label className="block">
          <span className="font-medium text-gray-700">Tipo de movimiento</span>
          <select
            value={kind}
            onChange={(event) => setKind(event.target.value)}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
          >
            <option value="">Sin definir</option>
            {KIND_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="font-medium text-gray-700">Cuenta</span>
          <select
            value={accountId}
            onChange={(event) => setAccountId(event.target.value ? Number(event.target.value) : '')}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
          >
            <option value="">Sin asignar</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="font-medium text-gray-700">Nota</span>
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={3}
            placeholder="Ej. Cooperación kermés del equipo"
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        </label>

        <label className="block">
          <span className="font-medium text-gray-700">Tags</span>
          <input
            value={tagsText}
            onChange={(event) => setTagsText(event.target.value)}
            placeholder="kermes, trabajo"
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
          <span className="text-xs text-gray-400">Separados por coma</span>
        </label>

        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={reimbursable}
            onChange={(event) => setReimbursable(event.target.checked)}
            className="rounded border-gray-300"
          />
          Reembolsable
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={excluded}
            onChange={(event) => setExcluded(event.target.checked)}
            className="rounded border-gray-300"
          />
          Excluir de gráficas y presupuesto
        </label>

        {transaction.reference ? (
          <p className="text-xs text-gray-500">Referencia: {transaction.reference}</p>
        ) : null}

        {save.isError ? (
          <p className="text-sm text-red-600">{(save.error as Error).message}</p>
        ) : null}

        <button
          type="button"
          onClick={() => save.mutate()}
          disabled={save.isPending}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {save.isPending ? 'Guardando...' : 'Guardar'}
        </button>
        <button
          type="button"
          onClick={() => {
            if (window.confirm('¿Borrar esta transacción? El saldo de la cuenta se revertirá si ya se había aplicado.')) {
              remove.mutate()
            }
          }}
          disabled={remove.isPending}
          className="w-full px-4 py-2 border border-red-200 text-red-700 rounded-lg hover:bg-red-50 disabled:opacity-50"
        >
          {remove.isPending ? 'Borrando...' : 'Borrar'}
        </button>
      </div>
    </aside>
  )
}
