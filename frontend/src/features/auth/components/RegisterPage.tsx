import { useAuthStore } from '@/stores/authStore'
import { Card } from '@/components/ui/card'
import { Sparkles } from 'lucide-react'
import { Navigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import RegisterForm from './RegisterForm'

export default function RegisterPage() {
    const { isAuthenticated } = useAuthStore()

    if (isAuthenticated) {
        return <Navigate to="/chat" replace />
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-background px-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className="w-full max-w-[400px] space-y-8"
            >
                <div className="flex flex-col items-center text-center space-y-4">
                    <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center shadow-xl shadow-primary/20">
                        <span className="text-2xl font-black text-primary-foreground">G</span>
                    </div>
                    <div className="space-y-1.5">
                        <h1 className="text-2xl font-bold tracking-tight text-foreground/90">Create Your Account</h1>
                        <p className="text-sm text-muted-foreground font-medium">Join the cosmic intelligence network.</p>
                    </div>
                </div>

                <Card className="p-8 shadow-2xl border-border/40 bg-card/50 backdrop-blur-sm">
                    <RegisterForm />

                    <div className="mt-8 pt-6 border-t border-border/50 text-center">
                        <p className="text-[13px] text-muted-foreground font-medium">
                            Already have an account? <Link to="/login" className="text-primary font-bold hover:underline">Sign In</Link>
                        </p>
                    </div>
                </Card>

                <div className="flex items-center justify-center gap-2 text-[11px] text-muted-foreground/40 font-bold uppercase tracking-widest">
                    <Sparkles className="w-3 h-3" />
                    Powered by Intelligence Layer 1.0
                </div>
            </motion.div>
        </div>
    )
}
