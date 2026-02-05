import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
    Moon, Sun, Target, Sparkles,
    Clock, Calendar, ChevronRight
} from "lucide-react";
import { cn } from '@/lib/utils';
import api from '@/lib/api';

interface UpcomingEvent {
    type: string;
    event_type: string;
    title: string;
    description: string;
    icon: string;
    datetime: string;
    timestamp: number;
    countdown: string;
    hours_until: number;
    category: string;
    // Optional fields based on event type
    sign?: string;
    planet?: string;
    planet_symbol?: string;
    aspect?: string;
    aspect_symbol?: string;
    transit_planet?: string;
    natal_planet?: string;
    new_sign?: string;
    old_sign?: string;
    is_outer_planet?: boolean;
    phase_name?: string;
    illumination?: number;
    exactness?: number;
}

interface UpcomingEventsResponse {
    events: UpcomingEvent[];
    generated_at: string;
    window_days: number;
}

// Category styling
const categoryConfig: Record<string, { bg: string; border: string; icon: React.ReactNode }> = {
    lunar: {
        bg: 'bg-slate-800/50',
        border: 'border-slate-500/30',
        icon: <Moon className="h-4 w-4 text-slate-300" />
    },
    planetary: {
        bg: 'bg-indigo-900/30',
        border: 'border-indigo-500/30',
        icon: <Sun className="h-4 w-4 text-amber-400" />
    },
    personal: {
        bg: 'bg-purple-900/30',
        border: 'border-purple-500/30',
        icon: <Target className="h-4 w-4 text-purple-400" />
    },
};

// Event type icons
const getEventIcon = (event: UpcomingEvent) => {
    switch (event.type) {
        case 'new_moon':
            return '🌑';
        case 'full_moon':
            return '🌕';
        case 'voc_end':
            return '✨';
        case 'ingress':
            return '🚀';
        case 'retrograde_start':
            return '↩️';
        case 'retrograde_end':
            return '➡️';
        case 'natal_transit':
            return '🎯';
        default:
            return event.icon || '⭐';
    }
};

// Urgency styling based on time until event
const getUrgencyStyle = (hoursUntil: number) => {
    if (hoursUntil <= 6) return 'ring-2 ring-amber-500/50 bg-amber-900/20';
    if (hoursUntil <= 24) return 'ring-1 ring-amber-500/30';
    return '';
};

const EventCard = ({ event }: { event: UpcomingEvent }) => {
    const config = categoryConfig[event.category] || categoryConfig.planetary;
    const urgencyStyle = getUrgencyStyle(event.hours_until);
    const eventDate = new Date(event.datetime);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={cn(
                "p-4 rounded-lg border transition-all duration-300 hover:scale-[1.02]",
                config.bg,
                config.border,
                urgencyStyle
            )}
        >
            <div className="flex items-start gap-3">
                {/* Event Icon */}
                <div className="text-2xl flex-shrink-0 mt-0.5">
                    {getEventIcon(event)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    {/* Title & Category */}
                    <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-white text-sm truncate">
                            {event.title}
                        </h3>
                        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-black/30 text-xs text-gray-400">
                            {config.icon}
                            {event.category}
                        </span>
                    </div>

                    {/* Description */}
                    <p className="text-xs text-gray-400 mb-2 line-clamp-2">
                        {event.description}
                    </p>

                    {/* Time Info */}
                    <div className="flex items-center gap-4 text-xs">
                        <span className="flex items-center gap-1 text-gray-300">
                            <Clock className="h-3 w-3" />
                            {event.countdown}
                        </span>
                        <span className="flex items-center gap-1 text-gray-500">
                            <Calendar className="h-3 w-3" />
                            {format(eventDate, 'MMM d, h:mm a')}
                        </span>
                    </div>

                    {/* Extra Info (aspect exactness, etc.) */}
                    {event.exactness !== undefined && (
                        <div className="mt-2 flex items-center gap-2">
                            <div className="h-1 flex-1 bg-gray-700 rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full bg-purple-500"
                                    initial={{ width: 0 }}
                                    animate={{ width: `${event.exactness * 100}%` }}
                                    transition={{ duration: 0.5 }}
                                />
                            </div>
                            <span className="text-xs text-purple-400">
                                {Math.round(event.exactness * 100)}% exact
                            </span>
                        </div>
                    )}
                </div>

                {/* Arrow */}
                <ChevronRight className="h-4 w-4 text-gray-600 flex-shrink-0" />
            </div>
        </motion.div>
    );
};

const TimelineEvent = ({ event }: { event: UpcomingEvent }) => {
    const eventDate = new Date(event.datetime);

    return (
        <div className="flex gap-4">
            {/* Timeline Line */}
            <div className="flex flex-col items-center">
                <div className={cn(
                    "w-3 h-3 rounded-full border-2",
                    event.hours_until <= 24 ? "bg-amber-500 border-amber-400" : "bg-gray-700 border-gray-600"
                )} />
                <div className="w-0.5 flex-1 bg-gray-700/50" />
            </div>

            {/* Event Content */}
            <div className="pb-6 flex-1">
                <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">{getEventIcon(event)}</span>
                    <span className="text-sm font-medium text-white">{event.title}</span>
                </div>
                <div className="text-xs text-gray-500">
                    {format(eventDate, 'EEEE, MMM d')} • {event.countdown}
                </div>
            </div>
        </div>
    );
};

type ViewMode = 'cards' | 'timeline' | 'compact';
type FilterCategory = 'all' | 'lunar' | 'planetary' | 'personal';

export const UpcomingEvents = ({
    days = 7,
    maxEvents = 10,
    showFilters = true,
    defaultView = 'cards'
}: {
    days?: number;
    maxEvents?: number;
    showFilters?: boolean;
    defaultView?: ViewMode;
}) => {
    const [viewMode, setViewMode] = React.useState<ViewMode>(defaultView);
    const [filterCategory, setFilterCategory] = React.useState<FilterCategory>('all');

    const { data, isLoading, error } = useQuery({
        queryKey: ['tracking-upcoming', days],
        queryFn: async () => {
            const res = await api.get<UpcomingEventsResponse>(`/api/v1/tracking/upcoming?days=${days}`);
            return res.data;
        },
        refetchInterval: 300000, // Refresh every 5 minutes
        staleTime: 60000,
    });

    const filteredEvents = React.useMemo(() => {
        if (!data?.events) return [];
        let events = data.events;
        
        if (filterCategory !== 'all') {
            events = events.filter(e => e.category === filterCategory);
        }
        
        return events.slice(0, maxEvents);
    }, [data?.events, filterCategory, maxEvents]);

    // Immediate events (next 24 hours)
    const immediateEvents = filteredEvents.filter(e => e.hours_until <= 24);

    if (isLoading) {
        return (
            <div className="p-6 bg-gray-900/50 rounded-xl border border-gray-800">
                <div className="animate-pulse space-y-4">
                    <div className="h-6 bg-gray-800 rounded w-1/3" />
                    <div className="h-20 bg-gray-800 rounded" />
                    <div className="h-20 bg-gray-800 rounded" />
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 bg-red-900/20 rounded-xl border border-red-800/50 text-red-400">
                <p>Failed to load upcoming events</p>
            </div>
        );
    }

    return (
        <div className="bg-gray-900/50 rounded-xl border border-gray-800 overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-600">
                        <Sparkles className="h-5 w-5 text-white" />
                    </div>
                    <div>
                        <h2 className="font-semibold text-white">Upcoming Events</h2>
                        <p className="text-xs text-gray-500">
                            {filteredEvents.length} events in next {days} days
                        </p>
                    </div>
                </div>

                {showFilters && (
                    <div className="flex items-center gap-2">
                        {/* Category Filter */}
                        <select
                            value={filterCategory}
                            onChange={(e) => setFilterCategory(e.target.value as FilterCategory)}
                            className="text-xs bg-gray-800 border border-gray-700 rounded-lg px-2 py-1 text-gray-300"
                        >
                            <option value="all">All Categories</option>
                            <option value="lunar">Lunar</option>
                            <option value="planetary">Planetary</option>
                            <option value="personal">Personal</option>
                        </select>

                        {/* View Toggle */}
                        <div className="flex bg-gray-800 rounded-lg p-0.5">
                            {(['cards', 'timeline', 'compact'] as ViewMode[]).map((mode) => (
                                <button
                                    key={mode}
                                    onClick={() => setViewMode(mode)}
                                    className={cn(
                                        "px-2 py-1 text-xs rounded transition-colors",
                                        viewMode === mode
                                            ? "bg-gray-700 text-white"
                                            : "text-gray-500 hover:text-gray-300"
                                    )}
                                >
                                    {mode.charAt(0).toUpperCase() + mode.slice(1)}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Immediate Alert Banner */}
            {immediateEvents.length > 0 && (
                <div className="px-4 py-2 bg-amber-900/20 border-b border-amber-800/30">
                    <div className="flex items-center gap-2 text-amber-400 text-sm">
                        <Clock className="h-4 w-4" />
                        <span className="font-medium">
                            {immediateEvents.length} event{immediateEvents.length > 1 ? 's' : ''} within 24 hours
                        </span>
                    </div>
                </div>
            )}

            {/* Content */}
            <div className="p-4">
                {filteredEvents.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        <Calendar className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No upcoming events in this category</p>
                    </div>
                ) : viewMode === 'cards' ? (
                    <div className="space-y-3">
                        <AnimatePresence mode="popLayout">
                            {filteredEvents.map((event, idx) => (
                                <EventCard key={`${event.type}-${event.timestamp}-${idx}`} event={event} />
                            ))}
                        </AnimatePresence>
                    </div>
                ) : viewMode === 'timeline' ? (
                    <div className="pl-2">
                        {filteredEvents.map((event, idx) => (
                            <TimelineEvent
                                key={`${event.type}-${event.timestamp}-${idx}`}
                                event={event}
                            />
                        ))}
                    </div>
                ) : (
                    /* Compact View */
                    <div className="divide-y divide-gray-800">
                        {filteredEvents.map((event, idx) => (
                            <div
                                key={`${event.type}-${event.timestamp}-${idx}`}
                                className="py-2 flex items-center justify-between hover:bg-gray-800/30 px-2 -mx-2 rounded transition-colors"
                            >
                                <div className="flex items-center gap-2">
                                    <span>{getEventIcon(event)}</span>
                                    <span className="text-sm text-white truncate max-w-[200px]">
                                        {event.title}
                                    </span>
                                </div>
                                <span className="text-xs text-gray-500">{event.countdown}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default UpcomingEvents;
