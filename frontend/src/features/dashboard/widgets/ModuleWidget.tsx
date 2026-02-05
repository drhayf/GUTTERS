
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Star, Hash, User, ArrowRight } from 'lucide-react'

interface ModuleData {
    name: string
    display_name: string
    summary_items: { label: string; value: string }[]
    status: 'active' | 'generating' | 'inactive'
}

interface ModuleWidgetProps {
    modules: ModuleData[]
}

export default function ModuleWidget({ modules }: ModuleWidgetProps) {
    const getIcon = (name: string) => {
        switch (name) {
            case 'astrology':
                return <Star className="h-5 w-5 text-purple-500" />
            case 'numerology':
                return <Hash className="h-5 w-5 text-blue-500" />
            case 'human_design':
                return <User className="h-5 w-5 text-amber-500" />
            default:
                return <Star className="h-5 w-5" />
        }
    }

    return (
        <Card className="h-full flex flex-col">
            <CardHeader>
                <CardTitle className="text-lg">My Design</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 space-y-4">
                {modules.map((mod) => (
                    <div key={mod.name} className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer group">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-background rounded-full border">
                                {getIcon(mod.name)}
                            </div>
                            <div>
                                <h4 className="font-medium text-sm">{mod.display_name}</h4>
                                <div className="flex gap-2 text-xs text-muted-foreground mt-1">
                                    {mod.summary_items.map((item, i) => (
                                        <span key={i} className="inline-flex items-center">
                                            {item.value}
                                            {i < mod.summary_items.length - 1 && <span className="mx-1.5 opacity-50">•</span>}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                ))}

                {modules.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground text-sm">
                        Calculating modules...
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
