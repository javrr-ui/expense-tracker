export interface BudgetItem {
  category_id: number
  category_name: string
  color: string
  budget: number
  spent: number
  remaining: number
  pct: number | null
}

export interface BudgetReport {
  year: number
  month: number
  items: BudgetItem[]
  total_spent: number
}
