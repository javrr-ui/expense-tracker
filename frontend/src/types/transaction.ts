export interface Transaction {
  transaction_id: number
  email_id: string
  date: string | null
  amount: number
  description: string
  type: string
  bank_id: number
  bank_name: string
  category_id: number | null
  subcategory_id: number | null
  merchant: string | null
  reference: string | null
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