import { motion } from 'framer-motion'
import { Shield } from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'

export interface UserRecord {
    id: number
    name: string
    username: string
    email: string
    created_at: string
    is_superuser: boolean
    profile_image_url: string | null
    uuid: string
    tier_id: number | null
}

interface UserCardProps {
    user: UserRecord
    isCurrentUser: boolean
    index: number
    onSelect: (user: UserRecord) => void
}

export default function UserCard({ user, isCurrentUser, index, onSelect }: UserCardProps) {
    return (
        <motion.button
            layout
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -30, height: 0 }}
            transition={{ delay: index * 0.04 }}
            onClick={() => onSelect(user)}
            className={`
                w-full text-left relative rounded-xl border transition-all duration-300
                active:scale-[0.98] cursor-pointer
                ${isCurrentUser
                    ? 'bg-primary/[0.03] border-primary/15 shadow-sm'
                    : 'bg-white/40 border-transparent hover:border-white/40 hover:shadow-sm'
                }
            `}
        >
            <div className="flex items-center gap-4 p-4">
                {/* Avatar */}
                <Avatar className={`h-10 w-10 border ${isCurrentUser ? 'border-primary/30' : 'border-white/60'} shadow-sm`}>
                    <AvatarImage src={`https://api.dicebear.com/7.x/notionists/svg?seed=${user.username}`} />
                    <AvatarFallback className="text-xs font-bold">
                        {user.username[0]?.toUpperCase()}
                    </AvatarFallback>
                </Avatar>

                {/* Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-foreground truncate">
                            {user.username}
                        </span>
                        {user.is_superuser && (
                            <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 font-bold tracking-wider border-amber-500/30 text-amber-600 bg-amber-500/5">
                                ADMIN
                            </Badge>
                        )}
                        {isCurrentUser && (
                            <span className="flex items-center gap-1">
                                <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                                <span className="text-[9px] font-bold uppercase tracking-widest text-primary">
                                    You
                                </span>
                            </span>
                        )}
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-muted-foreground truncate">
                            {user.email}
                        </span>
                        <span className="text-muted-foreground/30">·</span>
                        <span className="text-[10px] text-muted-foreground/60 font-mono whitespace-nowrap">
                            {new Date(user.created_at).toLocaleDateString('en-US', {
                                month: 'short', day: 'numeric', year: 'numeric'
                            })}
                        </span>
                    </div>
                </div>

                {/* Visual indicator */}
                {isCurrentUser && (
                    <Shield className="w-4 h-4 text-primary/20 shrink-0" />
                )}
            </div>
        </motion.button>
    )
}
