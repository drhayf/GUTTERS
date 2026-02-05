export interface Quest {
    id: number
    title: string
    description?: string
    recurrence: 'once' | 'daily' | 'weekly' | 'monthly' | 'custom'
    cron_expression?: string
    difficulty: number
    tags: string
    is_active: boolean
    source: 'user' | 'agent'
    job_id?: string
}

export interface QuestCreate {
    title: string
    description?: string
    recurrence: string
    cron_expression?: string
    difficulty: number
    tags: string[]
}

export interface QuestUpdate {
    title?: string
    recurrence?: string
    cron_expression?: string
    is_active?: boolean
}
