import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { Plus, RefreshCw, Search, Calendar, ChevronLeft, ChevronRight, Tags } from 'lucide-react'
import {
  assignTransactionCategory,
  getAccounts,
  getCategories,
  getTransactions,
  recategorizeTransactions,
  syncEmails,
} from '../lib/api'
import { formatMoney } from '../lib/format'
import { KIND_OPTIONS, kindLabel } from '../lib/kinds'
import type { Transaction } from '../types/transaction'
import CategoryPicker from './CategoryPicker'
import TransactionDetail from './TransactionDetail'
import TransactionForm from './TransactionForm'

const PAGE_SIZE = 25

export default function TransactionList() {
  const [page, setPage] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [accountId, setAccountId] = useState<number | ''>('')
  const [kind, setKind] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [tag, setTag] = useState('')
  const [uncategorizedOnly, setUncategorizedOnly] = useState(false)
  const [unassignedOnly, setUnassignedOnly] = useState(false)
  const [reimbursableOnly, setReimbursableOnly] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)

  const queryClient = useQueryClient()
  const offset = (page - 1) * PAGE_SIZE

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput)
      setPage(1)
    }, 300)
    return () => window.clearTimeout(timer)
  }, [searchInput])

  const { data, isLoading, error } = useQuery({
    queryKey: [
      'transactions',
      PAGE_SIZE,
      offset,
      uncategorizedOnly,
      unassignedOnly,
      accountId,
      kind,
      search,
      tag,
      reimbursableOnly,
      dateFrom,
      dateTo,
    ],
    queryFn: () =>
      getTransactions({
        limit: PAGE_SIZE,
        offset,
        uncategorized: uncategorizedOnly,
        unassigned: unassignedOnly,
        accountId,
        kind,
        search,
        tag,
        reimbursable: reimbursableOnly,
        dateFrom,
        dateTo,
      }),
  })

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
  })
  const { data: accounts = [] } = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
  })

  const transactions = data?.transactions ?? []
  const total = data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const selected = transactions.find((tx) => tx.transaction_id === selectedId) ?? null

  const syncMutation = useMutation({
    mutationFn: syncEmails,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['category-stats'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })

  const recategorizeMutation = useMutation({
    mutationFn: recategorizeTransactions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['category-stats'] })
    },
  })

  const assignMutation = useMutation({
    mutationFn: ({
      id,
      categoryId,
      subcategoryId,
    }: {
      id: number
      categoryId: number | null
      subcategoryId: number | null
    }) => assignTransactionCategory(id, categoryId, subcategoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['category-stats'] })
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
    },
  })

  const handlePageChange = (newPage: number) => {
    setPage(Math.max(1, Math.min(newPage, totalPages)))
  }

  const formatAmount = (tx: Transaction) => {
    const formatted = formatMoney(tx.amount, tx.currency || 'MXN')
    return tx.type === 'income' ? `+${formatted}` : formatted
  }

  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return '—'
    try {
      return format(parseISO(dateStr), 'dd/MM/yyyy HH:mm')
    } catch {
      return dateStr
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Transacciones</h2>
          <p className="text-sm text-gray-500 mt-1">
            {total} transacciones · Página {page} de {totalPages}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setShowForm((value) => !value)}
            className="inline-flex items-center gap-2 px-3 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm"
          >
            <Plus className="w-4 h-4" />
            Alta manual
          </button>
          <button
            onClick={() => recategorizeMutation.mutate()}
            disabled={recategorizeMutation.isPending}
            className="inline-flex items-center gap-2 px-3 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 text-sm"
          >
            <Tags className="w-4 h-4" />
            {recategorizeMutation.isPending ? 'Aplicando...' : 'Auto-categorizar'}
          </button>
          <button
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            {syncMutation.isPending ? 'Sincronizando...' : 'Sincronizar'}
          </button>
        </div>
      </div>

      {showForm ? <TransactionForm onClose={() => setShowForm(false)} /> : null}

      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-4">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Buscar</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Descripción, comercio o nota..."
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="lg:col-span-3">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Cuenta</label>
            <select
              value={accountId}
              onChange={(event) => {
                setAccountId(event.target.value ? Number(event.target.value) : '')
                setPage(1)
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-white"
            >
              <option value="">Todas</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </select>
          </div>
          <div className="lg:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Movimiento</label>
            <select
              value={kind}
              onChange={(event) => {
                setKind(event.target.value)
                setPage(1)
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-white"
            >
              <option value="">Todos</option>
              {KIND_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div className="lg:col-span-3">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Tag</label>
            <input
              value={tag}
              onChange={(event) => {
                setTag(event.target.value)
                setPage(1)
              }}
              placeholder="kermes"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div className="lg:col-span-3">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Desde</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="date"
                value={dateFrom}
                onChange={(event) => {
                  setDateFrom(event.target.value)
                  setPage(1)
                }}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>
          <div className="lg:col-span-3">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Hasta</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="date"
                value={dateTo}
                onChange={(event) => {
                  setDateTo(event.target.value)
                  setPage(1)
                }}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>
          <div className="lg:col-span-6 flex flex-wrap items-end gap-4 pb-1">
            <label className="inline-flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={uncategorizedOnly}
                onChange={(event) => {
                  setUncategorizedOnly(event.target.checked)
                  setPage(1)
                }}
                className="rounded border-gray-300"
              />
              Sin categoría
            </label>
            <label className="inline-flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={unassignedOnly}
                onChange={(event) => {
                  setUnassignedOnly(event.target.checked)
                  setPage(1)
                }}
                className="rounded border-gray-300"
              />
              Sin cuenta
            </label>
            <label className="inline-flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={reimbursableOnly}
                onChange={(event) => {
                  setReimbursableOnly(event.target.checked)
                  setPage(1)
                }}
                className="rounded border-gray-300"
              />
              Reembolsables
            </label>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-600">Error al cargar las transacciones</div>
        ) : transactions.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No se encontraron transacciones</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">Fecha</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">Cuenta</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">Descripción</th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">Categoría</th>
                  <th className="text-right px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">Monto</th>
                  <th className="text-center px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">Tipo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {transactions.map((tx: Transaction) => (
                  <tr
                    key={tx.transaction_id}
                    className={`hover:bg-gray-50 transition-colors cursor-pointer ${
                      selectedId === tx.transaction_id ? 'bg-blue-50' : ''
                    }`}
                    onClick={(event) => {
                      const target = event.target as HTMLElement
                      if (target.closest('select, button, input, textarea, form, option')) return
                      setSelectedId(tx.transaction_id)
                    }}
                  >
                    <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">{formatDateTime(tx.date)}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="font-medium">{tx.account_name || tx.bank_name}</div>
                      <div className="text-xs text-gray-400">{kindLabel(tx.kind)}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs">
                      <div className="truncate">{tx.description}</div>
                      {tx.notes ? <div className="text-xs text-gray-400 truncate">{tx.notes}</div> : null}
                      <div className="flex flex-wrap gap-1 mt-1">
                        {tx.reimbursable ? (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700">reembolsable</span>
                        ) : null}
                        {tx.excluded_from_budget ? (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">excluida</span>
                        ) : null}
                        {tx.tags?.map((item) => (
                          <span key={item} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                            #{item}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <CategoryPicker
                        categories={categories}
                        categoryId={tx.category_id}
                        subcategoryId={tx.subcategory_id}
                        disabled={assignMutation.isPending}
                        onChange={(categoryId, subcategoryId) =>
                          assignMutation.mutate({
                            id: tx.transaction_id,
                            categoryId,
                            subcategoryId,
                          })
                        }
                      />
                    </td>
                    <td
                      className={`px-6 py-4 text-sm font-semibold text-right whitespace-nowrap ${
                        tx.type === 'income' ? 'text-green-600' : 'text-gray-900'
                      }`}
                    >
                      <div>{formatAmount(tx)}</div>
                      {tx.currency && tx.currency !== 'MXN' && tx.amount_mxn ? (
                        <div className="text-[10px] font-normal text-gray-400">
                          ≈ {formatMoney(tx.amount_mxn, 'MXN')}
                        </div>
                      ) : null}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span
                        className={`inline-flex px-2.5 py-0.5 text-xs font-medium rounded-full ${
                          tx.type === 'income' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {tx.type === 'income' ? 'Ingreso' : 'Gasto'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between bg-white px-6 py-3 rounded-xl border border-gray-200 shadow-sm">
          <button
            onClick={() => handlePageChange(page - 1)}
            disabled={page <= 1}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Anterior
          </button>

          <div className="flex items-center gap-1">
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter((p) => {
                if (totalPages <= 7) return true
                if (p === 1 || p === totalPages) return true
                if (Math.abs(p - page) <= 1) return true
                return false
              })
              .reduce<(number | 'ellipsis')[]>((acc, p, idx, arr) => {
                if (idx > 0 && p - (arr[idx - 1] as number) > 1) {
                  acc.push('ellipsis')
                }
                acc.push(p)
                return acc
              }, [])
              .map((item, idx) =>
                item === 'ellipsis' ? (
                  <span key={`dots-${idx}`} className="px-2 text-gray-400">
                    ...
                  </span>
                ) : (
                  <button
                    key={item}
                    onClick={() => handlePageChange(item)}
                    className={`w-9 h-9 text-sm font-medium rounded-lg transition-colors ${
                      item === page ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    {item}
                  </button>
                )
              )}
          </div>

          <button
            onClick={() => handlePageChange(page + 1)}
            disabled={page >= totalPages}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Siguiente
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {selected ? <TransactionDetail transaction={selected} onClose={() => setSelectedId(null)} /> : null}
    </div>
  )
}
