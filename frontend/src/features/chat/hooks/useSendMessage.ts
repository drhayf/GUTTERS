import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useChatStore } from '@/stores/chatStore'
import api from '@/lib/api'

export function useSendMessage(conversationId: number | null) {
    const queryClient = useQueryClient()
    const { selectedModel } = useChatStore()

    return useMutation({
        mutationFn: async (message: string) => {
            const { data } = await api.post('/api/v1/chat/master/send', {
                message,
                session_id: conversationId,
                model_tier: selectedModel
            })
            return data
        },
        onSuccess: () => {
            // Invalidate messages to show new one
            queryClient.invalidateQueries({ queryKey: ['messages', conversationId] })
        }
    })
}
