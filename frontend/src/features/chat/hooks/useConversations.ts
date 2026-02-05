import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export function useConversations() {
    const queryClient = useQueryClient()

    const query = useQuery({
        queryKey: ['conversations'],
        queryFn: async () => {
            const { data } = await api.get('/api/v1/chat/conversations')
            return data.conversations
        }
    })

    const createConversation = useMutation({
        mutationFn: async (name: string) => {
            const { data } = await api.post('/api/v1/chat/conversation/create', { name })
            return data.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['conversations'] })
        }
    })

    const deleteConversation = useMutation({
        mutationFn: async (id: number) => {
            await api.delete(`/api/v1/chat/conversation/${id}`)
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['conversations'] })
        }
    })

    return {
        ...query,
        createConversation,
        deleteConversation
    }
}
