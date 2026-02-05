import MoodSlider from './MoodSlider'

interface ComponentRendererProps {
    component: {
        component_id: string
        component_type: string
        [key: string]: any
    }
}

export function ComponentRenderer({ component }: ComponentRendererProps) {
    switch (component.component_type) {
        case 'multi_slider':
            return <MoodSlider component={component as any} />

        // Add other component types here as they are implemented

        default:
            return (
                <div className="p-4 border border-border border-dashed rounded-lg text-xs text-muted-foreground italic">
                    Unsupported component type: {component.component_type}
                </div>
            )
    }
}
