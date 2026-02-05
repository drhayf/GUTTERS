import { useEffect, useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import type { Quest, QuestUpdate } from '../types'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

interface QuestEditorDialogProps {
    quest: Quest | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

export default function QuestEditorDialog({ quest, open, onOpenChange }: QuestEditorDialogProps) {
    const queryClient = useQueryClient()
    const [title, setTitle] = useState('')
    const [recurrence, setRecurrence] = useState('once')
    const [cron, setCron] = useState('')

    useEffect(() => {
        if (quest) {
            setTitle(quest.title)
            setRecurrence(quest.recurrence)
            setCron(quest.cron_expression || '')
        }
    }, [quest])

    const updateMutation = useMutation({
        mutationFn: async (vars: { id: number; data: QuestUpdate }) => {
            const res = await api.patch(`/api/v1/quests/${vars.id}`, vars.data)
            return res.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['quests'] })
            onOpenChange(false)
        },
    })

    const handleSave = () => {
        if (!quest) return

        updateMutation.mutate({
            id: quest.id,
            data: {
                title,
                // description is not updatable in backend yet? Manager UpdateQuest doesn't take description. 
                // Plan said: "Update schedule/title/strict_mode".
                // I'll skip description update for now to match backend, or just title/recurrence.
                recurrence: recurrence as any,
                cron_expression: recurrence === 'custom' ? cron : undefined,
            },
        })
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Edit Quest</DialogTitle>
                    <DialogDescription>
                        Modify the quest details. Scheduling changes will restart the recurrence cycle.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="title" className="text-right">
                            Title
                        </Label>
                        <Input
                            id="title"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="col-span-3"
                        />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label className="text-right">Recurrence</Label>
                        <Select value={recurrence} onValueChange={setRecurrence}>
                            <SelectTrigger className="col-span-3">
                                <SelectValue placeholder="Select Frequency" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="once">Once</SelectItem>
                                <SelectItem value="daily">Daily</SelectItem>
                                <SelectItem value="weekly">Weekly</SelectItem>
                                <SelectItem value="monthly">Monthly</SelectItem>
                                <SelectItem value="custom">Custom (Cron)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    {recurrence === 'custom' && (
                        <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="cron" className="text-right">
                                Cron
                            </Label>
                            <Input
                                id="cron"
                                value={cron}
                                onChange={(e) => setCron(e.target.value)}
                                className="col-span-3 font-mono text-sm"
                                placeholder="* * * * *"
                            />
                        </div>
                    )}
                </div>
                <DialogFooter>
                    <Button type="submit" onClick={handleSave} disabled={updateMutation.isPending}>
                        {updateMutation.isPending ? 'Saving...' : 'Save changes'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
