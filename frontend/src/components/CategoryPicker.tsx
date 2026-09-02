import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createSubcategory } from '../lib/api'
import type { Category } from '../types/category'

interface CategoryPickerProps {
  categories: Category[]
  categoryId: number | null
  subcategoryId: number | null
  disabled?: boolean
  onChange: (categoryId: number | null, subcategoryId: number | null) => void
}

export default function CategoryPicker({
  categories,
  categoryId,
  subcategoryId,
  disabled = false,
  onChange,
}: CategoryPickerProps) {
  const selected = categories.find((item) => item.id === categoryId)
  const subs = selected?.subcategories ?? []
  const [addingSub, setAddingSub] = useState(false)
  const [newSub, setNewSub] = useState('')
  const queryClient = useQueryClient()

  const addSub = useMutation({
    mutationFn: (name: string) => createSubcategory(categoryId as number, name),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
      setAddingSub(false)
      setNewSub('')
      onChange(categoryId, created.id)
    },
  })

  return (
    <div className="flex flex-col gap-1 min-w-[10rem]">
      <select
        disabled={disabled}
        value={categoryId ?? ''}
        onChange={(event) => {
          const value = event.target.value ? Number(event.target.value) : null
          onChange(value, null)
        }}
        className="text-xs px-2 py-1.5 border border-gray-300 rounded-lg bg-white max-w-[11rem]"
      >
        <option value="">Sin categoría</option>
        {categories.map((category) => (
          <option key={category.id} value={category.id}>
            {category.name}
          </option>
        ))}
      </select>
      {categoryId ? (
        addingSub ? (
          <form
            className="flex gap-1"
            onSubmit={(event) => {
              event.preventDefault()
              if (!newSub.trim()) return
              addSub.mutate(newSub.trim())
            }}
          >
            <input
              autoFocus
              value={newSub}
              onChange={(event) => setNewSub(event.target.value)}
              placeholder="Nombre"
              className="text-xs px-2 py-1.5 border border-gray-300 rounded-lg w-full max-w-[11rem]"
            />
            <button type="submit" className="text-xs text-blue-700" disabled={addSub.isPending}>
              OK
            </button>
          </form>
        ) : (
          <select
            disabled={disabled}
            value={subcategoryId ?? ''}
            onChange={(event) => {
              if (event.target.value === '__new__') {
                setAddingSub(true)
                return
              }
              const value = event.target.value ? Number(event.target.value) : null
              onChange(categoryId, value)
            }}
            className="text-xs px-2 py-1.5 border border-gray-300 rounded-lg bg-white max-w-[11rem]"
          >
            <option value="">Sin subcategoría</option>
            {subs.map((sub) => (
              <option key={sub.id} value={sub.id}>
                {sub.name}
              </option>
            ))}
            <option value="__new__">+ Nueva subcategoría…</option>
          </select>
        )
      ) : null}
    </div>
  )
}
