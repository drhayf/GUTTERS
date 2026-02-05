import { useEffect } from 'react'
import { RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from './stores/authStore'
import { router } from './router'
import { Toaster } from './components/ui/toaster'
import ReloadPrompt from './components/pwa/ReloadPrompt'
import { OfflineIndicator } from './components/pwa/OfflineIndicator'
import { GlobalEventsProvider } from './contexts/GlobalEventsContext'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
    }
  }
})

export default function App() {
  const checkAuth = useAuthStore((state) => state.checkAuth)

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return (
    <QueryClientProvider client={queryClient}>
      <GlobalEventsProvider>
        <OfflineIndicator />
        <RouterProvider router={router} />
        <ReloadPrompt />
        <Toaster />
      </GlobalEventsProvider>
    </QueryClientProvider>
  )
}
