import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronLeft } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/authStore'
import { toast } from '@/hooks/use-toast'
import api from '@/lib/api'

import UserCard from './components/UserCard'
import UserDetailSheet from './components/UserDetailSheet'
import type { UserRecord } from './components/UserCard'

interface UsersResponse {
    data: UserRecord[]
    total_count: number
    page: number
    items_per_page: number
    has_more: boolean
}

export default function UserManagementPage() {
    const navigate = useNavigate()
    const { user: currentUser } = useAuthStore()
    const queryClient = useQueryClient()
    const [selectedUser, setSelectedUser] = useState<UserRecord | null>(null)

    const { data: usersResponse, isLoading } = useQuery<UsersResponse>({
        queryKey: ['admin-users'],
        queryFn: async () => {
            const { data } = await api.get('/api/v1/users?items_per_page=100')
            return data
        }
    })

    const deleteMutation = useMutation({
        mutationFn: async (username: string) => {
            await api.delete(`/api/v1/admin/users/${username}`)
        },
        onSuccess: (_, username) => {
            queryClient.invalidateQueries({ queryKey: ['admin-users'] })
            setSelectedUser(null)
            toast({
                title: 'User Removed',
                description: `${username} has been permanently removed from the system.`
            })
        },
        onError: (error: any) => {
            toast({
                title: 'Action Failed',
                description: error.response?.data?.detail || 'Insufficient permissions or user not found.',
                variant: 'destructive'
            })
        }
    })

    const users = usersResponse?.data || []
    const totalCount = usersResponse?.total_count || 0
    const isCurrentUserSuperuser = users.find(u => u.username === currentUser?.username)?.is_superuser ?? false

    // Sort: current user first, then superusers, then alphabetical
    const sortedUsers = [...users].sort((a, b) => {
        if (a.username === currentUser?.username) return -1
        if (b.username === currentUser?.username) return 1
        if (a.is_superuser && !b.is_superuser) return -1
        if (!a.is_superuser && b.is_superuser) return 1
        return a.username.localeCompare(b.username)
    })

    return (
        <div className="h-full flex flex-col bg-background">
            {/* Header */}
            <div className="p-6 border-b border-border/40 backdrop-blur-md bg-background/50 sticky top-0 z-10 flex items-center gap-4">
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => navigate(-1)}
                    className="rounded-xl hover:bg-muted/50"
                >
                    <ChevronLeft className="w-5 h-5 text-muted-foreground" />
                </Button>
                <div>
                    <h1 className="text-xl font-bold tracking-tight">User Registry</h1>
                    <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                        System Administration
                    </p>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 pb-safe min-h-0">
                <div className="max-w-2xl mx-auto space-y-6 pb-12">
                    {/* Loading skeleton */}
                    {isLoading && (
                        <div className="space-y-3">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="h-20 bg-white/40 rounded-xl animate-pulse" />
                            ))}
                        </div>
                    )}

                    {/* User count */}
                    {!isLoading && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex items-center gap-2 text-xs font-medium text-muted-foreground px-1"
                        >
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="uppercase tracking-widest">
                                {totalCount} registered {totalCount === 1 ? 'user' : 'users'}
                            </span>
                        </motion.div>
                    )}

                    {/* User list */}
                    <div className="space-y-2">
                        <AnimatePresence mode="popLayout">
                            {sortedUsers.map((user, idx) => (
                                <UserCard
                                    key={user.username}
                                    user={user}
                                    isCurrentUser={user.username === currentUser?.username}
                                    index={idx}
                                    onSelect={setSelectedUser}
                                />
                            ))}
                        </AnimatePresence>
                    </div>

                    {/* Empty state */}
                    {!isLoading && users.length === 0 && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-center py-16 text-muted-foreground"
                        >
                            <p className="text-sm font-medium">No users found</p>
                        </motion.div>
                    )}
                </div>
            </div>

            {/* Detail Sheet */}
            <UserDetailSheet
                user={selectedUser}
                open={!!selectedUser}
                onOpenChange={(open) => { if (!open) setSelectedUser(null) }}
                isCurrentUser={selectedUser?.username === currentUser?.username}
                canDelete={isCurrentUserSuperuser}
                onDelete={(username) => deleteMutation.mutate(username)}
                isDeleting={deleteMutation.isPending}
            />
        </div>
    )
}
