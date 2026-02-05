import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export interface ProgressionStats {
    level: number
    rank: string
    experience_points: number
    xp_to_next_level: number
    sync_rate: number
    sync_rate_momentum: number
    streak_count: number
}

export function useProgressionStats() {
    return useQuery({
        queryKey: ['progression-stats'],
        queryFn: async () => {
            const res = await api.get<ProgressionStats>('/api/v1/progression/stats')
            return res.data
        }
    })
}
