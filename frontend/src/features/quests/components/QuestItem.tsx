import type { Quest } from '../types'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Sparkles, User, MoreHorizontal, Trash2, Edit2 } from 'lucide-react'
import cronstrue from 'cronstrue'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

interface QuestItemProps {
    quest: Quest
    onEdit: (quest: Quest) => void
}

export default function QuestItem({ quest, onEdit }: QuestItemProps) {
    const queryClient = useQueryClient()

    const deleteMutation = useMutation({
        mutationFn: async (id: number) => {
            await api.delete(`/api/v1/quests/${id}`)
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['quests'] })
        }
    })

    const getScheduleText = () => {
        if (quest.recurrence === 'once') return 'One-time'
        if (quest.recurrence === 'daily') return 'Daily'
        if (quest.recurrence === 'weekly') return 'Weekly'
        if (quest.recurrence === 'custom' && quest.cron_expression) {
            try {
                return cronstrue.toString(quest.cron_expression)
            } catch {
                return quest.cron_expression
            }
        }
        return quest.recurrence
    }

    return (
        <Card className="mb-2 hover:bg-muted/5 transition-colors">
            <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="flex-shrink-0">
                        {quest.source === 'agent' ? (
                            <div className="bg-purple-100 dark:bg-purple-900 p-2 rounded-full" title="AI Generated">
                                <Sparkles className="w-4 h-4 text-purple-600 dark:text-purple-300" />
                            </div>
                        ) : (
                            <div className="bg-blue-100 dark:bg-blue-900 p-2 rounded-full" title="User Defined">
                                <User className="w-4 h-4 text-blue-600 dark:text-blue-300" />
                            </div>
                        )}
                    </div>
                    <div>
                        <div className="font-medium flex items-center gap-2">
                            {quest.title}
                            {quest.source === 'agent' && (
                                <Badge variant="secondary" className="text-[10px] h-4 px-1">AI</Badge>
                            )}
                        </div>
                        <div className="text-sm text-muted-foreground flex items-center gap-2">
                            <span>{getScheduleText()}</span>
                            {quest.is_active ? (
                                <span className="w-2 h-2 rounded-full bg-green-500" title="Active"></span>
                            ) : (
                                <span className="w-2 h-2 rounded-full bg-gray-300" title="Inactive"></span>
                            )}
                        </div>
                    </div>
                </div>

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                            <span className="sr-only">Open menu</span>
                            <MoreHorizontal className="h-4 w-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => onEdit(quest)}>
                            <Edit2 className="mr-2 h-4 w-4" />
                            Edit
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                            onClick={() => deleteMutation.mutate(quest.id)}
                            className="text-red-600 focus:text-red-600"
                        >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </CardContent>
        </Card>
    )
}
