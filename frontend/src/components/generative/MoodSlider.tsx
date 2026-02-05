import { useState } from 'react'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, Loader2, Sparkles } from 'lucide-react'
import api from '@/lib/api'
import { useMutation, useQueryClient } from '@tanstack/react-query'

interface MoodSliderProps {
    component: {
        component_id: string
        multi_slider: {
            question: string
            sliders: Array<{
                id: string
                label: string
                min_value: number
                max_value: number
                min_label: string
                max_label: string
                emoji_scale?: Record<number, string>
            }>
            context?: string
        }
    }
}

export default function MoodSlider({ component }: MoodSliderProps) {
    const queryClient = useQueryClient()
    const [values, setValues] = useState<Record<string, number>>(
        component.multi_slider.sliders.reduce((acc, slider) => ({
            ...acc,
            [slider.id]: Math.floor((slider.max_value + slider.min_value) / 2)
        }), {})
    )

    const submitResponse = useMutation({
        mutationFn: async () => {
            await api.post('/api/v1/chat/component/submit', {
                component_id: component.component_id,
                component_type: 'multi_slider',
                slider_values: values,
                submitted_at: new Date().toISOString()
            })
        },
        onSuccess: () => {
            // Refresh messages to show the recorded response if needed
            queryClient.invalidateQueries({ queryKey: ['messages'] })
        }
    })

    const isSubmitted = submitResponse.isSuccess || !!(component as any).response
    const responseData = (component as any).response

    if (isSubmitted) {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
            >
                <Card className="p-4 bg-primary/5 border-primary/20 border-dashed">
                    <div className="space-y-3">
                        <div className="flex items-center gap-2.5 text-sm font-medium text-primary">
                            <Check className="w-4 h-4" />
                            <span>Response synchronized with your digital twin</span>
                        </div>

                        {/* Show persisted response summary */}
                        {responseData && (
                            <div className="pl-6 text-xs text-muted-foreground/80 space-y-1">
                                {responseData.slider_values && Object.entries(responseData.slider_values).map(([key, value]) => {
                                    const slider = component.multi_slider.sliders.find(s => s.id === key);
                                    return (
                                        <div key={key} className="flex justify-between max-w-[200px]">
                                            <span>{slider ? slider.label : key}:</span>
                                            <span className="font-mono font-bold text-primary/70">{String(value)}</span>
                                        </div>
                                    );
                                })}
                                {responseData.slider_value && (
                                    <div className="flex justify-between max-w-[200px]">
                                        <span>Rating:</span>
                                        <span className="font-mono font-bold text-primary/70">{String(responseData.slider_value)}</span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </Card>
            </motion.div>
        )
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
        >
            <Card className="p-6 md:p-8 shadow-md border-border/60">
                <div className="space-y-6">
                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-primary/60" />
                            <h3 className="text-base font-semibold text-foreground/90">{component.multi_slider.question}</h3>
                        </div>
                        {component.multi_slider.context && (
                            <p className="text-sm text-muted-foreground/80 leading-relaxed font-medium">{component.multi_slider.context}</p>
                        )}
                    </div>

                    <div className="space-y-8">
                        {component.multi_slider.sliders.map((slider) => (
                            <div key={slider.id} className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <label className="text-sm font-semibold text-foreground/70">{slider.label}</label>
                                    <div className="flex items-center gap-3">
                                        <AnimatePresence mode="wait">
                                            <motion.span
                                                key={values[slider.id]}
                                                initial={{ opacity: 0, y: 5 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, y: -5 }}
                                                className="text-2xl"
                                            >
                                                {slider.emoji_scale?.[values[slider.id]]}
                                            </motion.span>
                                        </AnimatePresence>
                                        <span className="text-sm font-bold w-6 text-right font-mono text-primary/80">
                                            {values[slider.id]}
                                        </span>
                                    </div>
                                </div>

                                <Slider
                                    min={slider.min_value}
                                    max={slider.max_value}
                                    step={1}
                                    value={[values[slider.id]]}
                                    onValueChange={(newValue) => setValues({
                                        ...values,
                                        [slider.id]: newValue[0]
                                    })}
                                    className="py-2"
                                />

                                <div className="flex justify-between text-[11px] font-bold tracking-tight text-muted-foreground/50 uppercase">
                                    <span>{slider.min_label}</span>
                                    <span>{slider.max_label}</span>
                                </div>
                            </div>
                        ))}
                    </div>

                    <Button
                        onClick={() => submitResponse.mutate()}
                        disabled={submitResponse.isPending}
                        className="w-full h-11 transition-all duration-200 shadow-lg shadow-primary/10 font-semibold"
                    >
                        {submitResponse.isPending ? (
                            <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Synchronizing...
                            </>
                        ) : (
                            'Save Progress'
                        )}
                    </Button>
                </div>
            </Card>
        </motion.div>
    )
}
