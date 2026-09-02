import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createTransaction, getAccounts, getBanks } from '../lib/api'
import { KIND_OPTIONS } from '../lib/kinds'

interface TransactionFormProps {
  onClose: () => void
}

export default function TransactionForm({ onClose }: TransactionFormProps) {
  const queryClient = useQueryClient()
  const [amount, setAmount] = useState('')
  const [type, setType] = useState<'expense' | 'income'>('expense')
  const [date, setDate] = useState('')
  const [description, setDescription] = useState('')
  const [accountId, setAccountId] = useState<number | ''>('')
  const [bankName, setBankName] = useState('')
  const [kind, setKind] = useState('purchase')
  const [notes, setNotes] = useState('')
  const [tagsText, setTagsText] = useState('')
  const [reimbursable, setReimbursable] = useState(false)
  const [excluded, setExcluded] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: accounts = [] } = useQuery({ queryKey: ['accounts'], queryFn: getAccounts })
  const { data: banks = [] } = useQuery({ queryKey: ['banks'], queryFn: getBanks })

  const selectedAccount = accounts.find((account) => account.id === accountId)

  const mutation = useMutation({
    mutationFn: () => {
      const resolvedBank = selectedAccount?.bank_name || bankName
      if (!resolvedBank) {
        throw new Error('Elige una cuenta o un banco')
      }
      return createTransaction({
        amount: Number(amount),
        type,
        bank_name: resolvedBank,
        description: description.trim(),
        date: date ? new Date(date).toISOString() : null,
        notes: notes.trim() || null,
        tags: tagsText
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
        kind: kind || null,
        account_id: accountId === '' ? null : Number(accountId),
        reimbursable,
        excluded_from_budget: excluded,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['category-stats'] })
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      onClose()
    },
    onError: (err: Error) => setError(err.message),
  })

  return (
    <form
      className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        setError(null)
        mutation.mutate()
      }}
    >
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-gray-900">Nueva transacción</h3>
        <button type="button" onClick={onClose} className="text-sm text-gray-500 hover:text-gray-800">
          Cerrar
        </button>
      </div>
      {error ? <div className="rounded-lg bg-red-50 text-red-700 px-3 py-2 text-sm">{error}</div> : null}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <label className="block text-sm">
          <span className="font-medium text-gray-700">Monto</span>
          <input
            required
            type="number"
            step="0.01"
            min="0"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium text-gray-700">Gasto / ingreso</span>
          <select
            value={type}
            onChange={(event) => setType(event.target.value as 'expense' | 'income')}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
          >
            <option value="expense">Gasto</option>
            <option value="income">Ingreso</option>
          </select>
        </label>
        <label className="block text-sm">
          <span className="font-medium text-gray-700">Fecha</span>
          <input
            type="datetime-local"
            value={date}
            onChange={(event) => setDate(event.target.value)}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        </label>
        <label className="block text-sm">
          <span className="font-medium text-gray-700">Tipo de movimiento</span>
          <select
            value={kind}
            onChange={(event) => setKind(event.target.value)}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg bg-white"
          >
            {KIND_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm sm:col-span-2">
          <span className="font-medium text-gray-700">Descripción</span>
          <input
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Ej. Cooperación kermés"
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        </label>
        <label className="block text-sm">
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
        <label className="block text-sm">
          <span className="font-medium text-gray-700">Banco</span>
          <select
            value={selectedAccount?.bank_name || bankName}
            onChange={(event) => setBankName(event.target.value)}
            disabled={Boolean(selectedAccount)}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg bg-white disabled:bg-gray-50"
          >
            <option value="">Elige banco</option>
            {banks.map((bank) => (
              <option key={bank.name} value={bank.name}>
                {bank.display_name}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm sm:col-span-2">
          <span className="font-medium text-gray-700">Nota</span>
          <input
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        </label>
        <label className="block text-sm sm:col-span-2">
          <span className="font-medium text-gray-700">Tags</span>
          <input
            value={tagsText}
            onChange={(event) => setTagsText(event.target.value)}
            placeholder="kermes, trabajo"
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg"
          />
        </label>
      </div>
      <div className="flex flex-wrap gap-4 text-sm">
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={reimbursable}
            onChange={(event) => setReimbursable(event.target.checked)}
            className="rounded border-gray-300"
          />
          Reembolsable
        </label>
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={excluded}
            onChange={(event) => setExcluded(event.target.checked)}
            className="rounded border-gray-300"
          />
          Excluir de gráficas y presupuesto
        </label>
      </div>
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={mutation.isPending || amount === ''}
          className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {mutation.isPending ? 'Guardando...' : 'Guardar'}
        </button>
      </div>
    </form>
  )
}
