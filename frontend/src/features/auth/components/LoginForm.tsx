import { useState } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function LoginForm() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [isPending, setIsPending] = useState(false)
    const [error, setError] = useState('')
    const { login } = useAuthStore()
    const navigate = useNavigate()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsPending(true)
        setError('')

        try {
            const formData = new FormData()
            formData.append('username', email)
            formData.append('password', password)

            await login(formData)
            navigate('/chat')
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Authentication failed. Please check your credentials.')
        } finally {
            setIsPending(false)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="email" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80 ml-1">Email or Username</Label>
                    <Input
                        id="email"
                        type="text"
                        placeholder="admin@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="h-11 bg-background focus-visible:ring-primary/20 transition-all border-border/80"
                        required
                    />
                </div>
                <div className="space-y-2">
                    <div className="flex items-center justify-between ml-1">
                        <Label htmlFor="password" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80">Password</Label>
                        <a href="#" className="text-[11px] font-bold text-primary hover:underline">Forgot?</a>
                    </div>
                    <Input
                        id="password"
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="h-11 bg-background focus-visible:ring-primary/20 transition-all border-border/80"
                        required
                    />
                </div>
            </div>

            {error && (
                <motion.p
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-[12px] font-semibold text-destructive text-center bg-destructive/5 py-2 rounded-md border border-destructive/10"
                >
                    {error}
                </motion.p>
            )}

            <Button
                type="submit"
                className="w-full h-11 font-bold tracking-tight text-[15px] shadow-lg shadow-primary/20 group transition-all duration-300"
                disabled={isPending}
            >
                {isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                    <span className="flex items-center justify-center gap-2">
                        Sign In <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </span>
                )}
            </Button>
        </form>
    )
}
