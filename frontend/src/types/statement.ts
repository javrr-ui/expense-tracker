export interface ReconcileItem {
  status: 'matched' | 'only_statement' | 'only_ledger' | string
  score: number
  statement_tx_id: number | null
  ledger_tx_id: number | null
  date: string | null
  amount: number
  statement_description: string | null
  ledger_description: string | null
  ledger_source: string | null
}

export interface ReconcileReport {
  statement_id: number
  account_id: number
  matched: number
  only_statement: number
  only_ledger: number
  items: ReconcileItem[]
  applied: boolean
  merged?: number
}

export interface Statement {
  id: number
  account_id: number
  period_start: string | null
  period_end: string | null
  previous_balance: number | null
  closing_balance: number | null
  minimum_payment: number | null
  due_date: string | null
  source: string
  status: string
  source_filename: string | null
  error: string | null
  parsed_at: string | null
}
