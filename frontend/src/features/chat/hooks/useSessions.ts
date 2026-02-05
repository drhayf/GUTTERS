import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export interface Session {
    id: number
    session_type: string
    name: string
    contribute_to_memory: boolean
    created_at: string
    updated_at: string
    context_id?: string
}

export function useSessions(sessionType?: string) {
    const queryClient = useQueryClient()

    const query = useQuery({
        queryKey: ['sessions', sessionType],
        queryFn: async () => {
            const params = sessionType ? { session_type: sessionType } : {}
            const { data } = await api.get('/api/v1/chat/sessions/list', { params })
            return data.sessions as Session[]
        }
    })

    const createSession = useMutation({
        mutationFn: async ({ name, type, contributeToMemory = true }: { name: string, type: string, contributeToMemory?: boolean }) => {
            const { data } = await api.post('/api/v1/chat/sessions/create', {
                name,
                session_type: type,
                contribute_to_memory: contributeToMemory
            })
            return data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sessions'] })
        }
    })

    return {
        ...query,
        createSession
    }
}
