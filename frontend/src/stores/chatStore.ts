import { create } from 'zustand'

interface ChatState {
    currentConversationId: number | null
    setCurrentConversationId: (id: number | null) => void
    selectedModel: 'standard' | 'premium'
    setSelectedModel: (model: 'standard' | 'premium') => void
}

export const useChatStore = create<ChatState>((set) => ({
    currentConversationId: null,
    setCurrentConversationId: (id) => set({ currentConversationId: id }),
    selectedModel: 'standard',
    setSelectedModel: (model) => set({ selectedModel: model })
}))
