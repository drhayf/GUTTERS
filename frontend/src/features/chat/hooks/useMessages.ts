import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export function useMessages(conversationId: number | null) {
    return useQuery({
        queryKey: ['messages', conversationId],
        queryFn: async () => {
            if (!conversationId) return []

            const { data } = await api.get(`/api/v1/chat/master/history?limit=100&session_id=${conversationId}`)
            // Note: The history endpoint currently returns all master chat history for user.
            // If session_id filtering is added later, we'll use it here.
            return data.history
        },
        enabled: !!conversationId,
        refetchInterval: false,
        refetchOnWindowFocus: false
    })
}
