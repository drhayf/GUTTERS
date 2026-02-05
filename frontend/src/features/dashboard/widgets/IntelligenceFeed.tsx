
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BrainCircuit, Zap, Lightbulb } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'

interface FeedItem {
    id: string
    type: 'pattern' | 'hypothesis'
    title: string
    description: string
    confidence: number
    timestamp: string
}

interface IntelligenceFeedProps {
    items: FeedItem[]
}

export default function IntelligenceFeed({ items }: IntelligenceFeedProps) {
    return (
        <Card className="h-full flex flex-col">
            <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                    <BrainCircuit className="h-5 w-5 text-emerald-500" />
                    Intelligence Feed
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0">
                <ScrollArea className="h-[300px] px-6">
                    <div className="space-y-4 pb-6">
                        {items.length === 0 ? (
                            <p className="text-sm text-muted-foreground text-center py-8">
                                Observing patterns...
                            </p>
                        ) : (
                            items.map((item) => (
                                <div key={item.id} className="flex gap-3 relative pb-4 last:pb-0">
                                    {/* Timeline line */}
                                    <div className="absolute left-[11px] top-8 bottom-0 w-px bg-border last:hidden" />

                                    <div className="relative z-10 mt-1">
                                        {item.type === 'pattern' ? (
                                            <div className="h-6 w-6 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center border border-blue-200 dark:border-blue-800">
                                                <Zap className="h-3.5 w-3.5" />
                                            </div>
                                        ) : (
                                            <div className="h-6 w-6 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 flex items-center justify-center border border-amber-200 dark:border-amber-800">
                                                <Lightbulb className="h-3.5 w-3.5" />
                                            </div>
                                        )}
                                    </div>

                                    <div className="space-y-1">
                                        <div className="flex items-center gap-2">
                                            <h4 className="text-sm font-semibold">{item.title}</h4>
                                            <span className="text-[10px] text-muted-foreground border px-1.5 py-0.5 rounded-full bg-muted/50">
                                                {Math.round(item.confidence * 100)}% confidence
                                            </span>
                                        </div>
                                        <p className="text-xs text-muted-foreground leading-relaxed">
                                            {item.description}
                                        </p>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    )
}
