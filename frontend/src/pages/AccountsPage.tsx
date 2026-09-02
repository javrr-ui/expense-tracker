import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import AccountForm from '../components/AccountForm'
import { createAccount, getAccounts } from '../lib/api'
import { formatMoney } from '../lib/format'
import type { AccountPayload } from '../types/account'

export default function AccountsPage() {
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
  })

  const mutation = useMutation({
    mutationFn: createAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setShowForm(false)
      setError(null)
    },
    onError: (err: Error) => setError(err.message),
  })

  const handleCreate = async (payload: AccountPayload) => {
    setError(null)
    await mutation.mutateAsync(payload)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Cuentas</h2>
          <p className="text-sm text-gray-500 mt-1">Tarjetas, préstamos, cheques y monederos.</p>
        </div>
        <button
          onClick={() => setShowForm((value) => !value)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
        >
          <Plus className="w-4 h-4" />
          Nueva cuenta
        </button>
      </div>

      {showForm ? (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h3 className="font-medium text-gray-900 mb-4">Alta de cuenta</h3>
          <AccountForm
            includeOpeningBalance
            submitLabel="Crear cuenta"
            saving={mutation.isPending}
            error={error}
            onSubmit={handleCreate}
            onCancel={() => {
              setShowForm(false)
              setError(null)
            }}
          />
        </div>
      ) : null}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : accounts.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center text-gray-500">
          No hay cuentas todavía.
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-600 uppercase">Cuenta</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-600 uppercase">Tipo</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-gray-600 uppercase">Saldo</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-600 uppercase">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {accounts.map((account) => (
                  <tr key={account.id} className="hover:bg-gray-50">
                    <td className="px-5 py-3">
                      <Link to={`/accounts/${account.id}`} className="font-medium text-blue-700 hover:underline">
                        {account.name}
                      </Link>
                      <p className="text-xs text-gray-500">
                        {account.bank_display_name}
                        {account.last_four ? ` · ${account.last_four}` : ''}
                      </p>
                    </td>
                    <td className="px-5 py-3 text-sm text-gray-700">{account.account_type_label}</td>
                    <td
                      className={`px-5 py-3 text-sm font-semibold text-right ${
                        account.is_liability ? 'text-red-700' : 'text-emerald-700'
                      }`}
                    >
                      {formatMoney(account.current_balance, account.currency)}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex px-2 py-0.5 text-xs rounded-full ${
                          account.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {account.is_active ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
