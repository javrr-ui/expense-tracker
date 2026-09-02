export interface Subcategory {
  id: number
  name: string
  category_id: number
  description: string | null
}

export interface Category {
  id: number
  name: string
  description: string | null
  color: string
  kind: string
  subcategories: Subcategory[]
}

export interface CategoryStatSub {
  subcategory_id: number | null
  subcategory_name: string
  amount: number
}

export interface CategoryStat {
  category_id: number | null
  category_name: string
  color: string
  kind: string
  amount: number
  pct: number
  subcategories: CategoryStatSub[]
}

export interface CategoryStats {
  total: number
  uncategorized: number
  categories: CategoryStat[]
}
