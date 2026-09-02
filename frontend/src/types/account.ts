export interface BalanceSnapshot {
  id: number
  amount: number
  as_of: string
  source: string
  note: string | null
}

export interface Account {
  id: number
  name: string
  bank_id: number
  bank_name: string
  bank_display_name: string
  account_type_id: number
  account_type: string
  account_type_label: string
  is_liability: boolean
  current_balance: number
  currency: string
  last_four: string | null
  credit_limit: number | null
  utilization: number | null
  apr: number
  minimum_payment: number | null
  due_date_day: number | null
  cutoff_date_day: number | null
  next_due_date: string | null
  payment_frequency: string | null
  payment_frequency_label: string | null
  recurrence_anchor: string | null
  recurrence_end: string | null
  remaining_payments: number | null
  scheduled_payments: ScheduledPayment[]
  is_active: boolean
  last_snapshot_at: string | null
  has_statement_password: boolean
  account_number: string | null
}

export interface AccountDetail extends Account {
  snapshots: BalanceSnapshot[]
}

export interface ScheduledPayment {
  date: string
  amount: number
  coverage?: string | null
}

export interface UpcomingPayment {
  account_id: number
  account_name: string
  bank_display_name: string
  amount: number
  due_date: string
  status: 'overdue' | 'due_soon' | 'upcoming' | 'minimum_paid' | 'paid_in_full' | string
}

export interface Dashboard {
  total_debt: number
  total_assets: number
  net_position: number
  liability_accounts: Account[]
  asset_accounts: Account[]
  upcoming_payments: UpcomingPayment[]
}

export interface AccountTypeOption {
  name: string
  label: string
  is_liability: boolean
}

export interface BankOption {
  name: string
  display_name: string
}

export interface AccountPayload {
  name: string
  bank_name: string
  account_type: string
  last_four?: string | null
  credit_limit?: number | null
  current_balance?: number
  currency?: string
  apr?: number
  minimum_payment?: number | null
  due_date_day?: number | null
  cutoff_date_day?: number | null
  payment_frequency?: string | null
  recurrence_anchor?: string | null
  recurrence_end?: string | null
  remaining_payments?: number | null
  statement_password?: string | null
  account_number?: string | null
  is_active?: boolean
}
