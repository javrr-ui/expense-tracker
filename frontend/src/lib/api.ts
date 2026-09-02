import type {
  Account,
  AccountDetail,
  AccountPayload,
  AccountTypeOption,
  BankOption,
  Dashboard,
} from '../types/account'
import type { BudgetReport } from '../types/budget'
import type { Category, CategoryStats } from '../types/category'
import type { ReconcileReport, Statement } from '../types/statement'
import type { PaginatedResponse, Transaction } from '../types/transaction'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })
  if (!response.ok) {
    let detail = 'Error de API'
    try {
      const body = await response.json()
      detail = body.detail ?? detail
    } catch {
      detail = response.statusText || detail
    }
    throw new Error(detail)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return response.json()
}

export interface TransactionQuery {
  limit?: number
  offset?: number
  uncategorized?: boolean
  unassigned?: boolean
  accountId?: number | ''
  kind?: string
  search?: string
  tag?: string
  reimbursable?: boolean
  dateFrom?: string
  dateTo?: string
}

export async function getTransactions(query: TransactionQuery = {}): Promise<PaginatedResponse> {
  const params = new URLSearchParams({
    limit: String(query.limit ?? 50),
    offset: String(query.offset ?? 0),
  })
  if (query.uncategorized) params.set('uncategorized', 'true')
  if (query.unassigned) params.set('unassigned', 'true')
  if (query.accountId) params.set('account_id', String(query.accountId))
  if (query.kind) params.set('kind', query.kind)
  if (query.search) params.set('search', query.search)
  if (query.tag) params.set('tag', query.tag)
  if (query.reimbursable) params.set('reimbursable', 'true')
  if (query.dateFrom) params.set('date_from', query.dateFrom)
  if (query.dateTo) params.set('date_to', query.dateTo)
  return request(`/transactions?${params}`)
}

export async function createTransaction(payload: {
  amount: number
  type: 'expense' | 'income'
  bank_name: string
  description?: string
  date?: string | null
  merchant?: string | null
  notes?: string | null
  tags?: string[]
  kind?: string | null
  account_id?: number | null
  excluded_from_budget?: boolean
  reimbursable?: boolean
}): Promise<Transaction> {
  return request('/transactions', {
    method: 'POST',
    body: JSON.stringify({ ...payload, source: 'manual' }),
  })
}

export async function deleteTransaction(id: number): Promise<void> {
  await request(`/transactions/${id}`, { method: 'DELETE' })
}

export async function syncEmails(): Promise<{ status: string }> {
  return request('/sync', { method: 'POST' })
}

export async function getDashboard(): Promise<Dashboard> {
  return request('/dashboard')
}

export async function getAccounts(): Promise<Account[]> {
  return request('/accounts')
}

export async function getAccount(id: number): Promise<AccountDetail> {
  return request(`/accounts/${id}`)
}

export async function createAccount(payload: AccountPayload): Promise<AccountDetail> {
  return request('/accounts', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateAccount(
  id: number,
  payload: AccountPayload
): Promise<AccountDetail> {
  return request(`/accounts/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function setPaymentCoverage(
  accountId: number,
  dueDate: string,
  status: string | null
): Promise<AccountDetail> {
  return request(`/accounts/${accountId}/payment-coverage`, {
    method: 'POST',
    body: JSON.stringify({ due_date: dueDate, status }),
  })
}

export async function setAccountBalance(
  id: number,
  amount: number,
  note?: string
): Promise<AccountDetail> {
  return request(`/accounts/${id}/balance`, {
    method: 'POST',
    body: JSON.stringify({ amount, note: note || null }),
  })
}

export async function getAccountTypes(): Promise<AccountTypeOption[]> {
  return request('/account-types')
}

export async function getBanks(): Promise<BankOption[]> {
  return request('/banks')
}

export async function getCategories(): Promise<Category[]> {
  return request('/categories')
}

export async function createCategory(payload: {
  name: string
  kind?: string
  color?: string
  description?: string | null
}): Promise<Category> {
  return request('/categories', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function createSubcategory(
  categoryId: number,
  name: string
): Promise<{ id: number; name: string; category_id: number; description: string | null }> {
  return request(`/categories/${categoryId}/subcategories`, {
    method: 'POST',
    body: JSON.stringify({ name }),
  })
}

export async function assignTransactionCategory(
  id: number,
  category_id: number | null,
  subcategory_id: number | null
): Promise<Transaction> {
  return request(`/transactions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ category_id, subcategory_id }),
  })
}

export async function updateTransaction(
  id: number,
  payload: {
    notes?: string | null
    tags?: string[]
    kind?: string | null
    account_id?: number | null
    category_id?: number | null
    subcategory_id?: number | null
    excluded_from_budget?: boolean
    reimbursable?: boolean
  }
): Promise<Transaction> {
  return request(`/transactions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function recategorizeTransactions(): Promise<{
  updated: number
  skipped_locked: number
}> {
  return request('/transactions/recategorize', { method: 'POST' })
}

export async function getCategoryStats(
  dateFrom?: string,
  dateTo?: string,
  txType: string = 'expense'
): Promise<CategoryStats> {
  const params = new URLSearchParams({ tx_type: txType })
  if (dateFrom) params.set('date_from', dateFrom)
  if (dateTo) params.set('date_to', dateTo)
  return request(`/stats/by-category?${params}`)
}

export async function getStatements(accountId?: number): Promise<Statement[]> {
  const params = new URLSearchParams()
  if (accountId) params.set('account_id', String(accountId))
  const suffix = params.toString() ? `?${params}` : ''
  return request(`/statements${suffix}`)
}

export async function uploadStatement(
  accountId: number,
  file: File,
  password?: string
): Promise<Statement> {
  const body = new FormData()
  body.append('account_id', String(accountId))
  body.append('file', file)
  if (password) body.append('password', password)
  const response = await fetch(`${API_BASE}/statements`, { method: 'POST', body })
  if (!response.ok) {
    let detail = 'Error de API'
    try {
      const json = await response.json()
      detail = json.detail ?? detail
    } catch {
      detail = response.statusText || detail
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function getStatementReconcile(id: number): Promise<ReconcileReport> {
  return request(`/statements/${id}/reconcile`)
}

export async function applyStatementReconcile(id: number): Promise<ReconcileReport> {
  return request(`/statements/${id}/reconcile`, { method: 'POST' })
}

export async function parseStatement(id: number, password?: string): Promise<Statement> {
  const body = new FormData()
  if (password) body.append('password', password)
  const response = await fetch(`${API_BASE}/statements/${id}/parse`, { method: 'POST', body })
  if (!response.ok) {
    let detail = 'Error de API'
    try {
      const json = await response.json()
      detail = json.detail ?? detail
    } catch {
      detail = response.statusText || detail
    }
    throw new Error(detail)
  }
  return response.json()
}

export async function getBudgets(year: number, month: number): Promise<BudgetReport> {
  return request(`/budgets?year=${year}&month=${month}`)
}

export async function upsertBudget(payload: {
  category_id: number
  year: number
  month: number
  amount: number
}): Promise<unknown> {
  return request('/budgets', {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}