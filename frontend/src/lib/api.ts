import type { PaginatedResponse } from '../types/transaction'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function getTransactions(
  limit: number = 50,
  offset: number = 0
): Promise<PaginatedResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  })

  const response = await fetch(`${API_BASE}/transactions?${params}`)
  if (!response.ok) {
    throw new Error('Error al obtener transacciones')
  }
  return response.json()
}

export async function syncEmails(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/sync`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error('Error al sincronizar')
  }
  return response.json()
}