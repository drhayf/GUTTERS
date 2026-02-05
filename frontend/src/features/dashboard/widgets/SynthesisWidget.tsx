
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Sparkles } from 'lucide-react'

interface SynthesisWidgetProps {
    synthesis?: string
    confidence?: number
}

export default function SynthesisWidget({ synthesis, confidence }: SynthesisWidgetProps) {
    return (
        <Card className="col-span-1 md:col-span-2 border-primary/20 bg-gradient-to-br from-background to-primary/5">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-xl font-bold font-serif flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-primary" />
                    Cosmic Manifesto
                </CardTitle>
                <div className="text-sm text-muted-foreground">
                    Confidence: {confidence ? Math.round(confidence * 100) : 0}%
                </div>
            </CardHeader>
            <CardContent>
                <p className="leading-relaxed text-lg">
                    {synthesis || "Aligning cosmic data..."}
                </p>
            </CardContent>
        </Card>
    )
}
