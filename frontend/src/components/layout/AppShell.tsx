import { Outlet, useLocation, useNavigate, useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
    LayoutDashboard,
    MessageSquare,
    BookOpen,
    User,
    Menu,
    LogOut,
    Settings,
    Loader2,
    Orbit,
    Hexagon,
    Sparkles
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useIsMobile } from '@/hooks/useMediaQuery'
import { useAuthStore } from '@/stores/authStore'
import { useChatStore } from '@/stores/chatStore'
import { useOnboardingStore } from '@/stores/onboardingStore'

import { useProgressionStats } from '@/hooks/useProgressionStats'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import ConversationSidebar from '@/components/chat/ConversationSidebar'
import { useEffect, useState } from 'react'

export default function AppShell() {
    const isMobile = useIsMobile()
    const location = useLocation()
    const navigate = useNavigate()
    const { user, logout, isAuthenticated, isLoading: authLoading } = useAuthStore()
    const { checkStatus } = useOnboardingStore()
    const { setCurrentConversationId } = useChatStore()
    const { conversationId } = useParams()

    const { data: stats } = useProgressionStats()

    const [isCheckingOnboarding, setIsCheckingOnboarding] = useState(true)

    // Sync Chat Store with URL
    useEffect(() => {
        if (conversationId) {
            setCurrentConversationId(Number(conversationId))
        } else {
            setCurrentConversationId(null)
        }
    }, [conversationId, setCurrentConversationId])

    // Onboarding Check Logic (Internal to Shell)
    useEffect(() => {
        const verify = async () => {
            if (isAuthenticated) {
                const complete = await checkStatus()
                // If not complete and not already ON onboarding, redirect
                if (!complete && !location.pathname.startsWith('/onboarding')) {
                    navigate('/onboarding', { replace: true })
                }
                // If complete and ON onboarding, redirect to chat (or dashboard)
                if (complete && location.pathname.startsWith('/onboarding')) {
                    navigate('/dashboard', { replace: true })
                }
            } else if (!authLoading && !isAuthenticated && !location.pathname.startsWith('/login') && !location.pathname.startsWith('/register')) {
                navigate('/login', { replace: true })
            }
            setIsCheckingOnboarding(false)
        }

        if (!authLoading) {
            verify()
        }
    }, [isAuthenticated, authLoading, checkStatus, location.pathname, navigate])

    const navItems = [
        { icon: LayoutDashboard, label: 'Board', path: '/dashboard' },
        { icon: Hexagon, label: 'Council', path: '/council' },
        { icon: Sparkles, label: 'Oracle', path: '/oracle' },
        { icon: Orbit, label: 'Tracking', path: '/tracking' },
        { icon: MessageSquare, label: 'Chat', path: '/chat' },
        { icon: BookOpen, label: 'Journal', path: '/journal' },
        { icon: User, label: 'Profile', path: '/profile' }
    ]

    const isLoadingState = authLoading || isCheckingOnboarding

    return (
        <div className="flex h-[100dvh] w-full max-w-[100vw] overflow-hidden bg-background text-foreground">
            {/* DESKTOP: Sidebar */}
            {!isMobile && (
                <aside className="w-[280px] border-r border-border/50 bg-card/30 backdrop-blur-xl hidden md:flex flex-col shrink-0 min-w-0">
                    <div className="h-14 flex items-center px-4 border-b border-border/50 justify-between">
                        <div className="flex items-center">
                            <div className="w-6 h-6 bg-primary rounded-md flex items-center justify-center mr-2 shadow-lg shadow-primary/20">
                                <span className="text-xs font-bold text-white">G</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="font-bold tracking-tight leading-none">GUTTERS</span>
                                {stats && (
                                    <div className="flex items-center gap-1.5 mt-0.5">
                                        <span className="text-[9px] bg-primary/10 text-primary px-1 py-px rounded font-mono-data font-medium leading-none">
                                            RANK {stats.rank}
                                        </span>
                                        <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${stats.sync_rate >= 0.8 ? 'bg-emerald-500' :
                                            stats.sync_rate >= 0.5 ? 'bg-amber-500' :
                                                'bg-red-500'
                                            }`} />
                                    </div>
                                )}
                            </div>
                        </div>
                        {/* User Dropdown (Desktop) */}
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full">
                                    <Avatar className="w-6 h-6 border border-border">
                                        <AvatarFallback className="bg-primary/5 text-primary/70 text-[10px]">
                                            {user?.username?.[0]?.toUpperCase()}
                                        </AvatarFallback>
                                    </Avatar>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-56">
                                <DropdownMenuItem onClick={() => navigate('/profile')}>
                                    <User className="w-4 h-4 mr-2" /> Profile
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => navigate('/control-room')}>
                                    <Settings className="w-4 h-4 mr-2" /> Control Room
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={logout} className="text-destructive">
                                    <LogOut className="w-4 h-4 mr-2" /> Log out
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>

                    <div className="flex-1 overflow-hidden flex flex-col">
                        {/* Integrated Chat Sidebar in Desktop Mode */}
                        <ConversationSidebar />
                    </div>
                </aside>
            )}

            {/* MAIN CONTENT AREA */}
            <div className="flex-1 flex flex-col h-full w-full min-w-0 overflow-hidden relative">

                {/* MOBILE: Top Bar (Sticky Glass) */}
                {isMobile && (
                    <header className="h-14 shrink-0 glass z-50 flex items-center justify-between px-4 safe-top sticky top-0 min-w-0 w-full">
                        <div className="flex items-center gap-3">
                            {/* Mobile Menu Trigger */}
                            <Sheet>
                                <SheetTrigger asChild>
                                    <Button variant="ghost" size="icon" className="-ml-2 h-9 w-9">
                                        <Menu className="w-5 h-5 text-foreground/70" />
                                    </Button>
                                </SheetTrigger>
                                <SheetContent side="left" className="w-[300px] p-0 border-r border-border">
                                    <ConversationSidebar />
                                </SheetContent>
                            </Sheet>

                            <div className="flex items-center gap-2">
                                <span className="font-bold tracking-tight text-sm">GUTTERS</span>
                                {/* Rank Badge */}
                                {stats && (
                                    <>
                                        <div className="h-4 w-[1px] bg-border/80 mx-1" />
                                        <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded font-mono-data font-medium">
                                            RANK {stats.rank}
                                        </span>
                                    </>
                                )}
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            {/* Sync Pulse */}
                            {/* Sync Pulse */}
                            {stats && (
                                <div className="flex items-center gap-1.5">
                                    <div className={`h-2 w-2 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.4)] ${stats.sync_rate >= 0.8 ? 'bg-emerald-500' :
                                        stats.sync_rate >= 0.5 ? 'bg-amber-500' :
                                            'bg-red-500'
                                        }`} />
                                    <span className="text-[10px] font-mono-data text-muted-foreground hidden xs:inline-block">SYNC</span>
                                </div>
                            )}
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full ml-1">
                                        <Avatar className="w-7 h-7 border border-border">
                                            <AvatarFallback className="bg-primary/5 text-primary/70 text-xs">
                                                {user?.email?.[0]?.toUpperCase()}
                                            </AvatarFallback>
                                        </Avatar>
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                    <DropdownMenuItem onClick={logout}>Log out</DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </div>
                    </header>
                )}

                {/* Scrollable Content Container */}
                {/* For chat, we don't want the main container scrollable - only internal message area */}
                <main className="flex-1 overflow-hidden relative min-w-0 w-full flex flex-col">
                    {isLoadingState ? (
                        <div className="h-full w-full flex items-center justify-center">
                            <Loader2 className="w-8 h-8 text-primary animate-spin opacity-50" />
                        </div>
                    ) : (
                        <>
                            <Outlet />
                            {/* Padding for bottom nav coverage on mobile */}
                            {isMobile && <div className="h-24" />}
                        </>
                    )}
                </main>

                {/* MOBILE: Bottom Nav (Sticky Glass) */}
                {isMobile && (
                    <nav className="shrink-0 glass border-t border-white/20 z-50 safe-bottom fixed bottom-0 left-0 right-0">
                        {/* We use fixed here to ensure it stays above everything even if main scrolls weirdly, though flex usually handles it.
                             However, standard tab bars often benefit from fixed positioning for z-index layering vs scrolling content.
                             The Layout structure uses flex-col, so 'sticky' block is better if the parent is h-full.
                             But let's stick to the REQUESTED MainLayout structure which was just a div at the bottom of the flex column.
                             Wait, MainLayout had it as a flex child. sticking to that.
                         */}
                        <div className="flex items-center justify-around h-16">
                            {navItems.map((item) => {
                                const isActive = location.pathname.startsWith(item.path)
                                return (
                                    <button
                                        key={item.path}
                                        onClick={() => navigate(item.path)}
                                        className="relative flex flex-col items-center justify-center w-full h-full"
                                    >
                                        {isActive && (
                                            <motion.div
                                                layoutId="nav-pill"
                                                className="absolute top-1 w-8 h-1 bg-primary rounded-full shadow-[0_0_10px_rgba(124,58,237,0.4)]"
                                            />
                                        )}
                                        <item.icon
                                            className={cn(
                                                "w-6 h-6 transition-colors duration-200",
                                                isActive ? "text-primary" : "text-zinc-400"
                                            )}
                                        />
                                        <span className={cn(
                                            "text-[10px] mt-1 font-medium transition-colors",
                                            isActive ? "text-primary" : "text-zinc-400"
                                        )}>
                                            {item.label}
                                        </span>
                                    </button>
                                )
                            })}
                        </div>
                    </nav>
                )}
            </div>
        </div>
    )
}
