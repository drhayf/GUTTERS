import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export default function RegisterForm() {
    const [name, setName] = useState('')
    const [username, setUsername] = useState('')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [isPending, setIsPending] = useState(false)
    const [error, setError] = useState('')
    const navigate = useNavigate()
    const { toast } = useToast()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsPending(true)
        setError('')

        try {
            await api.post('/api/v1/user', {
                name,
                username: username.toLowerCase(),
                email: email.toLowerCase(),
                password
            })

            toast({
                title: "Registration successful",
                description: "You can now sign in with your new account.",
            })

            navigate('/login')
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Registration failed. Please try again.')
        } finally {
            setIsPending(false)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="name" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80 ml-1">Full Name</Label>
                    <Input
                        id="name"
                        type="text"
                        placeholder="User Userson"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="h-11 bg-background focus-visible:ring-primary/20 transition-all border-border/80"
                        required
                        minLength={2}
                    />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="username" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80 ml-1">Username</Label>
                    <Input
                        id="username"
                        type="text"
                        placeholder="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="h-11 bg-background focus-visible:ring-primary/20 transition-all border-border/80"
                        required
                        pattern="^[a-z0-9]+$"
                        title="Username must be lowercase alphanumeric"
                        minLength={2}
                    />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="email" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80 ml-1">Email Address</Label>
                    <Input
                        id="email"
                        type="email"
                        placeholder="user@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="h-11 bg-background focus-visible:ring-primary/20 transition-all border-border/80"
                        required
                    />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="password" className="text-xs font-bold uppercase tracking-wider text-muted-foreground/80 ml-1">Password</Label>
                    <Input
                        id="password"
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="h-11 bg-background focus-visible:ring-primary/20 transition-all border-border/80"
                        required
                        minLength={8}
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
                        Register Account <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </span>
                )}
            </Button>
        </form>
    )
}
