import { useState } from 'react'

import { ActiveReflections } from './components/ActiveReflections'
import { ContextualComposer } from './components/ContextualComposer'
import { JournalEntryList } from './components/JournalEntryList'
import { CosmicContextWidget } from './components/CosmicContextWidget'

// We need an interface for Prompt from ActiveReflections
interface ReflectionPrompt {
    id: number
    prompt_text: string
    topic: string
    status: string
    created_at: string
}

export default function JournalPage() {
    const [selectedPrompt, setSelectedPrompt] = useState<ReflectionPrompt | null>(null)

    return (
        <div className="h-full overflow-y-auto overflow-x-hidden bg-gradient-to-b from-background to-muted/20 pb-safe-offset-bottom w-full min-w-0">
            <div className="max-w-2xl mx-auto px-4 pt-6 pb-20 space-y-8 w-full min-w-0">

                {/* 0. Cosmic Context - Current Conditions */}
                <section>
                    <CosmicContextWidget className="mb-2" />
                </section>

                {/* 1. Active Reflections Carousel */}
                <section>
                    <ActiveReflections
                        onSelectPrompt={setSelectedPrompt}
                        selectedPrompt={selectedPrompt}
                    />
                </section>

                {/* 2. Contextual Composer */}
                <section className="sticky top-4 z-10">
                    <ContextualComposer
                        replyingTo={selectedPrompt}
                        onCancelReply={() => setSelectedPrompt(null)}
                    />
                </section>

                {/* 3. Living Archive */}
                <section>
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold tracking-tight">Living Archive</h2>
                        {/* Filter controls could go here */}
                    </div>
                    <JournalEntryList />
                </section>
            </div>
        </div>
    )
}
