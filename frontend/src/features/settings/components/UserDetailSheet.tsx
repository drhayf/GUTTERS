import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Mail, Calendar, Hash, Fingerprint, Crown, AlertTriangle, Trash2, Copy, Check } from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetDescription,
} from '@/components/ui/sheet'
import type { UserRecord } from './UserCard'

/* ─── Detail Row ─────────────────────────────────────────────────────────── */

interface DetailRowProps {
    icon: React.ReactNode
    label: string
    value: string
    mono?: boolean
    copyable?: boolean
}

function DetailRow({ icon, label, value, mono, copyable }: DetailRowProps) {
    const [copied, setCopied] = useState(false)

    const handleCopy = () => {
        navigator.clipboard.writeText(value)
        setCopied(true)
        setTimeout(() => setCopied(false), 1500)
    }

    return (
        <div className="flex items-start gap-3 py-3 border-b border-border/30 last:border-0">
            <div className="mt-0.5 text-muted-foreground/50">{icon}</div>
            <div className="flex-1 min-w-0">
                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 mb-0.5">
                    {label}
                </p>
                <p className={`text-sm text-foreground break-all ${mono ? 'font-mono text-xs' : ''}`}>
                    {value}
                </p>
            </div>
            {copyable && (
                <button
                    onClick={handleCopy}
                    className="mt-1 p-1 rounded-md text-muted-foreground/40 hover:text-muted-foreground transition-colors"
                >
                    {copied
                        ? <Check className="w-3.5 h-3.5 text-emerald-500" />
                        : <Copy className="w-3.5 h-3.5" />
                    }
                </button>
            )}
        </div>
    )
}

/* ─── Delete Confirmation ────────────────────────────────────────────────── */

interface DeleteSectionProps {
    username: string
    isPending: boolean
    onDelete: () => void
}

function DeleteSection({ username, isPending, onDelete }: DeleteSectionProps) {
    const [confirmed, setConfirmed] = useState(false)

    return (
        <div className="mt-6 pt-4 border-t border-destructive/10">
            <AnimatePresence mode="wait">
                {!confirmed ? (
                    <motion.div
                        key="trigger"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <Button
                            variant="ghost"
                            onClick={() => setConfirmed(true)}
                            className="w-full h-11 rounded-xl text-destructive/60 hover:text-destructive hover:bg-destructive/5 transition-colors gap-2"
                        >
                            <Trash2 className="w-4 h-4" />
                            <span className="text-sm font-medium">Remove User</span>
                        </Button>
                    </motion.div>
                ) : (
                    <motion.div
                        key="confirm"
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        className="rounded-xl bg-destructive/5 border border-destructive/15 p-4 space-y-3"
                    >
                        <div className="flex items-start gap-3">
                            <AlertTriangle className="w-5 h-5 text-destructive mt-0.5 shrink-0" />
                            <div>
                                <p className="text-sm font-semibold text-foreground">
                                    Permanently remove {username}?
                                </p>
                                <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                                    This will delete all associated data including profile, readings,
                                    quests, and tracking history. This action cannot be undone.
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 justify-end">
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setConfirmed(false)}
                                disabled={isPending}
                                className="h-8 text-xs rounded-lg"
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="destructive"
                                size="sm"
                                onClick={onDelete}
                                disabled={isPending}
                                className="h-8 text-xs rounded-lg"
                            >
                                {isPending ? 'Removing...' : 'Remove Permanently'}
                            </Button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

/* ─── User Detail Sheet ──────────────────────────────────────────────────── */

interface UserDetailSheetProps {
    user: UserRecord | null
    open: boolean
    onOpenChange: (open: boolean) => void
    isCurrentUser: boolean
    canDelete: boolean
    onDelete: (username: string) => void
    isDeleting: boolean
}

export default function UserDetailSheet({
    user,
    open,
    onOpenChange,
    isCurrentUser,
    canDelete,
    onDelete,
    isDeleting,
}: UserDetailSheetProps) {
    if (!user) return null

    const formatFullDate = (dateStr: string) => {
        const d = new Date(dateStr)
        return d.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
            year: 'numeric',
        })
    }

    const formatTime = (dateStr: string) => {
        const d = new Date(dateStr)
        return d.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
        })
    }

    const truncateUuid = (uuid: string) => {
        if (!uuid || uuid.length < 12) return uuid
        return `${uuid.slice(0, 8)}...${uuid.slice(-4)}`
    }

    const roleName = user.is_superuser ? 'Administrator' : 'Standard User'
    const roleIcon = user.is_superuser
        ? <Crown className="w-3.5 h-3.5 text-amber-500" />
        : <Shield className="w-3.5 h-3.5" />

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent side="bottom" className="rounded-t-2xl max-h-[85vh] overflow-y-auto pb-safe">
                <SheetHeader className="text-center pb-2">
                    {/* Avatar */}
                    <div className="flex justify-center mb-3">
                        <Avatar className={`h-20 w-20 border-2 ${isCurrentUser ? 'border-primary/30' : 'border-border/40'} shadow-lg`}>
                            <AvatarImage src={`https://api.dicebear.com/7.x/notionists/svg?seed=${user.username}`} />
                            <AvatarFallback className="text-2xl font-bold">
                                {user.username[0]?.toUpperCase()}
                            </AvatarFallback>
                        </Avatar>
                    </div>

                    {/* Name & badges */}
                    <div className="flex items-center justify-center gap-2">
                        <SheetTitle className="text-lg">
                            {user.name || user.username}
                        </SheetTitle>
                        {user.is_superuser && (
                            <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 font-bold tracking-wider border-amber-500/30 text-amber-600 bg-amber-500/5">
                                ADMIN
                            </Badge>
                        )}
                        {isCurrentUser && (
                            <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 font-bold tracking-wider border-primary/30 text-primary bg-primary/5">
                                YOU
                            </Badge>
                        )}
                    </div>

                    <SheetDescription className="text-xs">
                        @{user.username}
                    </SheetDescription>
                </SheetHeader>

                {/* Detail rows */}
                <div className="mt-4 space-y-0">
                    <DetailRow
                        icon={<Mail className="w-4 h-4" />}
                        label="Email"
                        value={user.email}
                        copyable
                    />
                    <DetailRow
                        icon={roleIcon}
                        label="Role"
                        value={roleName}
                    />
                    <DetailRow
                        icon={<Hash className="w-4 h-4" />}
                        label="User ID"
                        value={String(user.id)}
                        mono
                    />
                    <DetailRow
                        icon={<Fingerprint className="w-4 h-4" />}
                        label="UUID"
                        value={truncateUuid(user.uuid)}
                        mono
                        copyable
                    />
                    <DetailRow
                        icon={<Calendar className="w-4 h-4" />}
                        label="Registered"
                        value={`${formatFullDate(user.created_at)} at ${formatTime(user.created_at)}`}
                    />
                </div>

                {/* Delete section — only for non-self, superuser-only */}
                {canDelete && !isCurrentUser && (
                    <DeleteSection
                        username={user.username}
                        isPending={isDeleting}
                        onDelete={() => onDelete(user.username)}
                    />
                )}

                {/* Self-protection notice */}
                {isCurrentUser && (
                    <div className="mt-6 pt-4 border-t border-border/30">
                        <div className="flex items-center gap-2 justify-center text-muted-foreground/40">
                            <Shield className="w-4 h-4" />
                            <span className="text-xs font-medium">Active session — protected</span>
                        </div>
                    </div>
                )}
            </SheetContent>
        </Sheet>
    )
}
