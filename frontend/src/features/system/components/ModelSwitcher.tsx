import { useState, useEffect } from 'react'
import { Sparkles, Brain, Save, AlertTriangle, Settings2, ChevronDown, Check, Coins, Gauge } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Slider } from '@/components/ui/slider'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import api from '@/lib/api'
import { toast } from '@/hooks/use-toast'
import { motion, AnimatePresence } from 'framer-motion'
import NotificationManager from '@/features/settings/NotificationManager'

interface ModelConfig {
    model_id: string
    temperature: number
    max_tokens: number
    cost_per_1k_input: number
    cost_per_1k_output: number
}

interface SystemConfig {
    models: Record<string, ModelConfig>
    exchange_rate: number
}

const PREMIUM_PRESETS = [
    { id: 'openai/gpt-oss-120b:free', name: 'GPT-OSS 120B (Premium Master)', cost_in: 0.0, cost_out: 0.0 },
    { id: 'anthropic/claude-sonnet-4.5', name: 'Claude 4.5 Sonnet (Original Premium)', cost_in: 0.003, cost_out: 0.015 },
    { id: 'deepseek/deepseek-r1', name: 'DeepSeek R1 (Deep Reasoning)', cost_in: 0.0, cost_out: 0.0 },
    { id: 'meta-llama/llama-3.3-70b-instruct', name: 'Llama 3.3 70B (High Precision)', cost_in: 0.0, cost_out: 0.0 },
]

const STANDARD_PRESETS = [
    { id: 'google/gemma-3-27b', name: 'Gemma 3 27B (Google SOTA)', cost_in: 0.0, cost_out: 0.0 },
    { id: 'anthropic/claude-haiku-4.5', name: 'Claude 4.5 Haiku (Original Standard)', cost_in: 0.00025, cost_out: 0.00125 },
    { id: 'qwen/qwen-2.5-vl-7b-instruct:free', name: 'Qwen 2.5 VL (Vision Specialized)', cost_in: 0.0, cost_out: 0.0 },
    { id: 'mistralai/mistral-small-3.1-24b-instruct', name: 'Mistral Small 3 (Efficient)', cost_in: 0.0, cost_out: 0.0 },
]

export default function ModelSwitcher() {
    const [config, setConfig] = useState<SystemConfig | null>(null)
    const [editingTier, setEditingTier] = useState<string | null>(null)
    const [editForm, setEditForm] = useState<ModelConfig | null>(null)
    const [loading, setLoading] = useState(false)

    const fetchConfig = async () => {
        try {
            const resp = await api.get('/api/v1/system/status')
            setConfig(resp.data.ai_config)
        } catch (err) {
            console.error('Failed to fetch AI config:', err)
        }
    }

    useEffect(() => {
        fetchConfig()
    }, [])

    const startEdit = (tier: string) => {
        setEditingTier(tier)
        setEditForm({ ...config!.models[tier] })
    }

    const saveEdit = async () => {
        if (!editingTier || !editForm) return
        setLoading(true)

        try {
            const resp = await api.put('/api/v1/system/config/ai', {
                tier: editingTier,
                ...editForm
            })

            if (resp.status === 200) {
                // High-Fidelity Verification: Fetch fresh config and verify synchronization
                const verifyResp = await api.get('/api/v1/system/status')
                const activeModel = verifyResp.data.ai_config.models[editingTier]

                if (activeModel.model_id === editForm.model_id) {
                    toast({
                        title: "Orchestration Synchronized",
                        description: `Verified: ${editingTier} tier is now actively running ${activeModel.model_id.split('/').pop()}. Settings persisted to database.`,
                        variant: "default"
                    })
                } else {
                    toast({
                        title: "Persistence Mismatch",
                        description: "Changes were saved to DB but in-memory reload failed. Please restart the engine.",
                        variant: "destructive"
                    })
                }

                setConfig(verifyResp.data.ai_config)
                setEditingTier(null)
            }
        } catch (err) {
            toast({ title: "Update Failed", variant: "destructive", description: "Failed to persist model configuration." })
        } finally {
            setLoading(false)
        }
    }

    const applyPreset = (preset: typeof PREMIUM_PRESETS[0]) => {
        if (!editForm) return
        setEditForm({
            ...editForm,
            model_id: preset.id,
            cost_per_1k_input: preset.cost_in,
            cost_per_1k_output: preset.cost_out
        })
    }

    if (!config) return (
        <div className="flex items-center justify-center p-12">
            <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
                <Settings2 className="w-8 h-8 text-primary opacity-50" />
            </motion.div>
        </div>
    )

    return (
        <div className="space-y-8 max-w-5xl mx-auto">
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between"
            >
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-primary/10 rounded-xl">
                        <Settings2 className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                        <h3 className="text-xl font-bold tracking-tight text-foreground">Model Orchestration</h3>
                        <p className="text-xs text-muted-foreground font-medium uppercase tracking-widest">Configure SOTA Intelligence Tiers</p>
                    </div>
                </div>
                <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/30 border border-border">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Backend Synchronized</span>
                </div>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {Object.entries(config.models).map(([tier, model]) => (
                    <motion.div
                        key={tier}
                        layout
                        className="relative"
                    >
                        <div className={`p-8 rounded-[2rem] border transition-all duration-500 overflow-hidden group ${tier === 'premium'
                            ? 'bg-gradient-to-br from-primary/10 via-primary/5 to-background border-primary/20 shadow-[0_0_50px_-12px_rgba(var(--primary),0.15)]'
                            : 'bg-gradient-to-br from-blue-500/10 via-blue-500/5 to-background border-blue-500/20 shadow-[0_0_50px_-12px_rgba(59,130,246,0.15)]'
                            }`}>
                            {/* Decorative Background Accents */}
                            <div className={`absolute -top-24 -right-24 w-48 h-48 rounded-full blur-[80px] opacity-20 ${tier === 'premium' ? 'bg-primary' : 'bg-blue-500'}`} />

                            <div className="relative z-10">
                                <div className="flex items-start justify-between mb-8">
                                    <div className="flex items-center gap-4">
                                        <div className={`p-3 rounded-2xl ${tier === 'premium' ? 'bg-primary/20 text-primary shadow-[0_0_20px_rgba(var(--primary),0.3)]' : 'bg-blue-500/20 text-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.3)]'
                                            }`}>
                                            {tier === 'premium' ? <Sparkles className="w-6 h-6" /> : <Brain className="w-6 h-6" />}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <h4 className="font-black uppercase tracking-[0.2em] text-[10px] opacity-70">{tier} Tier</h4>
                                                {tier === 'premium' && <span className="text-[8px] bg-primary/20 text-primary px-1.5 py-0.5 rounded-md font-bold uppercase tracking-wider">High Fidelity</span>}
                                            </div>
                                            <p className="text-lg font-bold tracking-tight mt-1 line-clamp-1">{model.model_id.split('/').pop()}</p>
                                        </div>
                                    </div>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => startEdit(tier)}
                                        className="h-8 text-[11px] font-bold uppercase tracking-widest border-foreground/10 hover:bg-foreground hover:text-background transition-colors"
                                    >
                                        Configure
                                    </Button>
                                </div>

                                <div className="space-y-6">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-4 rounded-2xl bg-secondary/20 border border-border/50">
                                            <div className="flex items-center gap-2 text-muted-foreground mb-1">
                                                <Gauge className="w-3 h-3" />
                                                <span className="text-[9px] font-bold uppercase tracking-widest">Temperature</span>
                                            </div>
                                            <p className="text-sm font-mono font-bold">{model.temperature.toFixed(2)}</p>
                                        </div>
                                        <div className="p-4 rounded-2xl bg-secondary/20 border border-border/50">
                                            <div className="flex items-center gap-2 text-muted-foreground mb-1">
                                                <Coins className="w-3 h-3" />
                                                <span className="text-[9px] font-bold uppercase tracking-widest">Est. Cost / 1k</span>
                                            </div>
                                            <p className="text-sm font-mono font-bold">${(model.cost_per_1k_input + model.cost_per_1k_output).toFixed(4)}</p>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 overflow-hidden">
                                        <div className="w-2 h-2 rounded-full bg-primary/30 shrink-0" />
                                        <p className="text-[10px] font-mono text-muted-foreground truncate">{model.model_id}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Edit Overlay */}
                        <AnimatePresence>
                            {editingTier === tier && (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    className="absolute inset-0 z-20 rounded-[2rem] bg-background/90 backdrop-blur-xl border-2 border-primary/50 p-8 flex flex-col shadow-2xl overflow-y-auto scrollbar-hide"
                                >
                                    <div className="flex-1 space-y-6">
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm font-black uppercase tracking-[0.2em] text-primary">Configuration</p>
                                            <div className="px-2 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-wider">{tier}</div>
                                        </div>

                                        <div className="space-y-4">
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-70 px-1">Active Model Preset</label>
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <Button variant="outline" className="w-full justify-between h-10 bg-secondary/20 border-border/50 font-mono text-xs">
                                                            {editForm?.model_id.split('/').pop()} <ChevronDown className="w-4 h-4 opacity-50" />
                                                        </Button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent className="w-64 bg-background/95 backdrop-blur-xl border-primary/20">
                                                        {(tier === 'premium' ? PREMIUM_PRESETS : STANDARD_PRESETS).map(preset => (
                                                            <DropdownMenuItem
                                                                key={preset.id}
                                                                onClick={() => applyPreset(preset)}
                                                                className="flex flex-col items-start gap-1 p-3 cursor-pointer hover:bg-primary/10 focus:bg-primary/10"
                                                            >
                                                                <div className="flex items-center gap-2 w-full justify-between">
                                                                    <span className="font-bold text-[11px] truncate">{preset.name}</span>
                                                                    {editForm?.model_id === preset.id && <Check className="w-3 h-3 text-primary" />}
                                                                </div>
                                                                <span className="text-[9px] font-mono text-muted-foreground opacity-60">{preset.id}</span>
                                                            </DropdownMenuItem>
                                                        ))}
                                                        <div className="h-px bg-border my-1" />
                                                        <DropdownMenuItem className="text-[10px] font-bold py-2 opacity-50 cursor-default">Custom Model Support Enabled Below</DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </div>

                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-70 px-1">Model Override Path</label>
                                                <Input
                                                    value={editForm?.model_id}
                                                    onChange={e => setEditForm(prev => ({ ...prev!, model_id: e.target.value }))}
                                                    className="h-10 text-xs font-mono bg-secondary/50 border-primary/20 focus:border-primary"
                                                    placeholder="provider/model-id"
                                                />
                                            </div>

                                            <div className="space-y-4 pt-2">
                                                <div className="flex items-center justify-between px-1">
                                                    <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-70">Creativity (Temp)</label>
                                                    <span className="text-[10px] font-mono font-bold bg-secondary px-2 py-0.5 rounded text-primary">{editForm?.temperature.toFixed(2)}</span>
                                                </div>
                                                <Slider
                                                    value={[editForm?.temperature || 0]}
                                                    min={0}
                                                    max={2}
                                                    step={0.05}
                                                    onValueChange={([v]) => setEditForm(prev => ({ ...prev!, temperature: v }))}
                                                />
                                            </div>

                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="space-y-2">
                                                    <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground opacity-70 px-1">In Cost / 1k</label>
                                                    <Input
                                                        type="number"
                                                        value={editForm?.cost_per_1k_input}
                                                        onChange={e => setEditForm(prev => ({ ...prev!, cost_per_1k_input: parseFloat(e.target.value) }))}
                                                        className="h-9 text-xs font-mono bg-secondary/50"
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground opacity-70 px-1">Out Cost / 1k</label>
                                                    <Input
                                                        type="number"
                                                        value={editForm?.cost_per_1k_output}
                                                        onChange={e => setEditForm(prev => ({ ...prev!, cost_per_1k_output: parseFloat(e.target.value) }))}
                                                        className="h-9 text-xs font-mono bg-secondary/50"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex gap-3 mt-8">
                                        <Button
                                            size="sm"
                                            onClick={saveEdit}
                                            disabled={loading}
                                            className="flex-1 font-black uppercase text-[10px] tracking-[0.2em] gap-2 h-10 shadow-[0_0_20px_rgba(var(--primary),0.3)]"
                                        >
                                            {loading ? <div className="w-3 h-3 border-2 border-background border-t-transparent rounded-full animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                                            Verify & Persist Configuration
                                        </Button>
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => setEditingTier(null)}
                                            className="font-bold uppercase text-[10px] tracking-widest text-muted-foreground hover:text-foreground h-10"
                                        >
                                            Discard
                                        </Button>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                ))}
            </div>

            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="p-6 rounded-3xl border border-amber-500/10 bg-gradient-to-r from-amber-500/5 to-transparent flex gap-4 backdrop-blur-sm"
            >
                <div className="p-2 bg-amber-500/10 rounded-lg shrink-0 h-fit">
                    <AlertTriangle className="w-5 h-5 text-amber-500" />
                </div>
                <div className="space-y-2">
                    <p className="text-[11px] font-black text-amber-500 uppercase tracking-[0.2em]">Synchronization & Persistence</p>
                    <p className="text-[11px] text-muted-foreground leading-relaxed font-medium">
                        Model changes are now <span className="text-foreground font-bold italic">permanently persisted</span> to the system configuration database. Overrides will survive server restarts and take effect immediately across all intelligence modules, from the Query Engine to the Background Observer.
                    </p>
                </div>
            </motion.div>

            <NotificationManager />
        </div>
    )
}
