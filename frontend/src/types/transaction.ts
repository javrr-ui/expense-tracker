export interface Transaction {
  transaction_id: number
  email_id: string
  date: string | null
  amount: number
  description: string
  type: string
  kind: string | null
  bank_id: number
  bank_name: string
  account_id: number | null
  account_name: string | null
  category_id: number | null
  subcategory_id: number | null
  category_name: string | null
  subcategory_name: string | null
  category_color: string | null
  category_source: string | null
  category_locked: boolean
  merchant: string | null
  reference: string | null
  notes: string | null
  tags: string[]
  source: string | null
  balance_applied: boolean
  excluded_from_budget: boolean
  reimbursable: boolean
  currency: string
  amount_mxn: number | null
}

export interface PaginatedResponse {
  total: number
  transactions: Transaction[]
}

export interface TransactionFilters {
  search: string
  bank: string
  type: string
  dateFrom: string
  dateTo: string
}