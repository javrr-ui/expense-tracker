import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { createCategory, createSubcategory, getCategories } from '../lib/api'

const KINDS = [
  { value: 'expense', label: 'Gasto' },
  { value: 'income', label: 'Ingreso' },
  { value: 'transfer', label: 'Transferencia / deuda' },
]

const COLORS = ['#f97316', '#3b82f6', '#8b5cf6', '#ef4444', '#ec4899', '#14b8a6', '#64748b', '#0ea5e9', '#22c55e', '#eab308']

export default function CategoriesPage() {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [kind, setKind] = useState('expense')
  const [color, setColor] = useState(COLORS[0])
  const [error, setError] = useState<string | null>(null)
  const [subNames, setSubNames] = useState<Record<number, string>>({})

  const { data: categories = [], isLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['categories'] })
    queryClient.invalidateQueries({ queryKey: ['category-stats'] })
    queryClient.invalidateQueries({ queryKey: ['transactions'] })
  }

  const createCat = useMutation({
    mutationFn: createCategory,
    onSuccess: () => {
      setName('')
      setError(null)
      invalidate()
    },
    onError: (err: Error) => setError(err.message),
  })

  const createSub = useMutation({
    mutationFn: ({ categoryId, subName }: { categoryId: number; subName: string }) =>
      createSubcategory(categoryId, subName),
    onSuccess: (_data, variables) => {
      setSubNames((current) => ({ ...current, [variables.categoryId]: '' }))
      setError(null)
      invalidate()
    },
    onError: (err: Error) => setError(err.message),
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-gray-900">Categorías</h2>
        <p className="text-sm text-gray-500 mt-1">
          Crea categorías y subcategorías. Luego aparecen en Transacciones para clasificar.
        </p>
      </div>

      <form
        className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4"
        onSubmit={(event) => {
          event.preventDefault()
          if (!name.trim()) return
          createCat.mutate({ name: name.trim(), kind, color })
        }}
      >
        <h3 className="font-medium text-gray-900">Nueva categoría</h3>
        {error ? <div className="rounded-lg bg-red-50 text-red-700 px-3 py-2 text-sm">{error}</div> : null}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <input
            required
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Ej. Social / trabajo"
            className="sm:col-span-2 px-3 py-2 border border-gray-300 rounded-lg"
          />
          <select
            value={kind}
            onChange={(event) => setKind(event.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white"
          >
            {KINDS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={color}
              onChange={(event) => setColor(event.target.value)}
              className="h-10 w-12 border border-gray-300 rounded cursor-pointer"
            />
            <button
              type="submit"
              disabled={createCat.isPending}
              className="inline-flex items-center gap-1 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
              Agregar
            </button>
          </div>
        </div>
      </form>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {categories.map((category) => (
            <section key={category.id} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-3 h-3 rounded-full" style={{ background: category.color }} />
                <h3 className="font-semibold text-gray-900">{category.name}</h3>
                <span className="text-xs text-gray-400">
                  {KINDS.find((item) => item.value === category.kind)?.label ?? category.kind}
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {category.subcategories.length === 0 ? (
                  <span className="text-xs text-gray-400">Sin subcategorías</span>
                ) : (
                  category.subcategories.map((sub) => (
                    <span key={sub.id} className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                      {sub.name}
                    </span>
                  ))
                )}
              </div>
              <form
                className="flex gap-2"
                onSubmit={(event) => {
                  event.preventDefault()
                  const subName = (subNames[category.id] ?? '').trim()
                  if (!subName) return
                  createSub.mutate({ categoryId: category.id, subName })
                }}
              >
                <input
                  value={subNames[category.id] ?? ''}
                  onChange={(event) =>
                    setSubNames((current) => ({ ...current, [category.id]: event.target.value }))
                  }
                  placeholder="Nueva subcategoría, ej. Eventos"
                  className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-lg"
                />
                <button
                  type="submit"
                  disabled={createSub.isPending}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Añadir
                </button>
              </form>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
