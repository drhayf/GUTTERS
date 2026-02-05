
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Moon, Sun, Activity } from 'lucide-react'

interface CosmicData {
    moon_phase: string
    moon_sign: string
    sun_sign: string
    active_transits_count: number
    geomagnetic_index: number
}

interface CosmicWidgetProps {
    data?: CosmicData
}

export default function CosmicWidget({ data }: CosmicWidgetProps) {
    if (!data) return <Card className="h-full animate-pulse" />

    return (
        <Card className="h-full">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                    <Activity className="h-5 w-5" />
                    Current Conditions
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-3">
                        <Moon className="h-5 w-5 text-indigo-400" />
                        <div>
                            <p className="text-sm font-medium">Moon Phase</p>
                            <p className="text-xs text-muted-foreground">{data.moon_phase}</p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-3">
                        <Sun className="h-5 w-5 text-amber-500" />
                        <div>
                            <p className="text-sm font-medium">Sun Sign</p>
                            <p className="text-xs text-muted-foreground">{data.sun_sign}</p>
                        </div>
                    </div>
                </div>

                <div className="text-xs text-center text-muted-foreground mt-4">
                    {data.active_transits_count} active planetary transits
                    <br />
                    Geomagnetic Kp Index: {data.geomagnetic_index}
                </div>
            </CardContent>
        </Card>
    )
}
