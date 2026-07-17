import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TransactionList from './components/TransactionList'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xl">ET</span>
                </div>
                <h1 className="text-2xl font-semibold text-gray-900">Expense Tracker</h1>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <TransactionList />
        </main>
      </div>
    </QueryClientProvider>
  )
}

export default App
