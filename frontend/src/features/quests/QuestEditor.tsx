
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Repeat, Activity, Tag } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

import api from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Badge } from '@/components/ui/badge'

const formSchema = z.object({
    title: z.string().min(1, "Title is required"),
    description: z.string().optional(),
    recurrence: z.enum(["once", "daily", "weekly", "monthly", "custom"]),
    difficulty: z.enum(["easy", "medium", "hard", "elite"]),
    tags: z.string().optional() // Comma separated input
})

interface Quest {
    id: number
    title: string
    description?: string
    recurrence: string
    difficulty: string // API returns string enum often or mapped int? Read model says int, but manager uses Enum. Let's check API. API QuestRead says difficulty: int. Manager uses Enum. API might serialize Enum to string?
    // Wait, quests.py QuestRead says difficulty: int.
    // Manager create_quest handles QuestDifficulty enum.
    // If API response model says int, it might fail validation if Enum is returned?
    // Let's assume int 1-4 based on XP_MAP order if serialized. Or string "easy".
    // Safest is to treat as any for display until verified.
    source: string
    is_active: boolean
}

export default function QuestEditor() {
    const queryClient = useQueryClient()
    const [isOpen, setIsOpen] = useState(false)

    // Fetch Quests
    const { data: quests, isLoading } = useQuery({
        queryKey: ['quests-admin'],
        queryFn: async () => {
            const res = await api.get<Quest[]>('/api/v1/quests?view=definitions')
            return res.data
        }
    })

    // Create Quest Mutation
    const createQuest = useMutation({
        mutationFn: async (values: z.infer<typeof formSchema>) => {
            // Map difficulty string to 1-4 int if needed, or pass string if API accepts Enum.
            // API QuestCreate schema: difficulty: int = 1.
            // So I must map Enum string to Int.
            const diffMap: Record<string, number> = { "easy": 1, "medium": 2, "hard": 3, "elite": 4 }

            const payload = {
                title: values.title,
                description: values.description,
                recurrence: values.recurrence.toLowerCase(),
                difficulty: diffMap[values.difficulty] || 1,
                tags: values.tags ? values.tags.split(',').map(t => t.trim()) : []
            }
            const res = await api.post('/api/v1/quests/', payload)
            return res.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['quests-admin'] })
            queryClient.invalidateQueries({ queryKey: ['quests'] }) // Dashboard
            setIsOpen(false)
            form.reset()
        }
    })

    // Delete Quest Mutation
    const deleteQuest = useMutation({
        mutationFn: async (id: number) => {
            await api.delete(`/api/v1/quests/${id}`)
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['quests-admin'] })
            queryClient.invalidateQueries({ queryKey: ['quests'] })
        }
    })

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            title: "",
            recurrence: "once",
            difficulty: "easy",
            tags: ""
        }
    })

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-lg font-bold">Quest Database</h2>
                    <p className="text-xs text-muted-foreground">Manage system and user directives</p>
                </div>
                <Dialog open={isOpen} onOpenChange={setIsOpen}>
                    <DialogTrigger asChild>
                        <Button size="sm" className="gap-2">
                            <Plus className="w-4 h-4" /> New Quest
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Create New Quest</DialogTitle>
                        </DialogHeader>
                        <Form {...form}>
                            <form onSubmit={form.handleSubmit((data) => createQuest.mutate(data))} className="space-y-4">
                                <FormField
                                    control={form.control}
                                    name="title"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Title</FormLabel>
                                            <FormControl>
                                                <Input placeholder="e.g. Morning Meditation" {...field} />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                                <div className="grid grid-cols-2 gap-4">
                                    <FormField
                                        control={form.control}
                                        name="recurrence"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Recurrence</FormLabel>
                                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                                    <FormControl>
                                                        <SelectTrigger>
                                                            <SelectValue placeholder="Select recurrence" />
                                                        </SelectTrigger>
                                                    </FormControl>
                                                    <SelectContent>
                                                        <SelectItem value="once">Once</SelectItem>
                                                        <SelectItem value="daily">Daily</SelectItem>
                                                        <SelectItem value="weekly">Weekly</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="difficulty"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Rank</FormLabel>
                                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                                    <FormControl>
                                                        <SelectTrigger>
                                                            <SelectValue placeholder="Select rank" />
                                                        </SelectTrigger>
                                                    </FormControl>
                                                    <SelectContent>
                                                        <SelectItem value="easy">Easy (E)</SelectItem>
                                                        <SelectItem value="medium">Medium (D-C)</SelectItem>
                                                        <SelectItem value="hard">Hard (B-A)</SelectItem>
                                                        <SelectItem value="elite">Elite (S)</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>
                                <div className="flex justify-end gap-2 pt-2">
                                    <Button type="button" variant="ghost" onClick={() => setIsOpen(false)}>Cancel</Button>
                                    <Button type="submit" disabled={createQuest.isPending}>
                                        {createQuest.isPending ? "Creating..." : "Construct Quest"}
                                    </Button>
                                </div>
                            </form>
                        </Form>
                    </DialogContent>
                </Dialog>
            </div>

            {/* Quest List */}
            <div className="grid gap-3">
                <AnimatePresence>
                    {quests?.map((quest) => (
                        <motion.div
                            key={quest.id}
                            layout
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="bg-secondary/10 border border-border/50 rounded-lg p-3 flex items-center gap-3 group"
                        >
                            <div className="p-2 bg-background rounded border border-border/50 text-muted-foreground">
                                <Activity className="w-4 h-4" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className="font-medium text-sm text-foreground">{quest.title}</span>
                                    <Badge variant="outline" className="text-[10px] h-5 px-1.5 font-normal text-muted-foreground">
                                        RANK {quest.difficulty}
                                    </Badge>
                                </div>
                                <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
                                    <div className="flex items-center gap-1">
                                        <Repeat className="w-3 h-3" /> {quest.recurrence}
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Tag className="w-3 h-3" /> {quest.source}
                                    </div>
                                </div>
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive hover:bg-destructive/10"
                                onClick={() => deleteQuest.mutate(quest.id)}
                            >
                                <Trash2 className="w-4 h-4" />
                            </Button>
                        </motion.div>
                    ))}
                </AnimatePresence>
                {!isLoading && quests?.length === 0 && (
                    <div className="text-center py-8 text-sm text-muted-foreground border-2 border-dashed border-border/30 rounded-lg">
                        No active directives found.
                    </div>
                )}
            </div>
        </div>
    )
}
