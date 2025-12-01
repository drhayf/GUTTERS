"""
Journaling Domain - Core Domain for Self-Reflection and Insight Capture

The Journaling domain is a CORE DOMAIN that provides:
- Entry creation and management
- Emotion detection and tracking
- Theme and pattern analysis
- Personalized prompt generation
- Integration with Digital Twin traits

This is a CORE DOMAIN following the Fractal Extensibility Pattern.

Architecture:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ┌─────────────────────────────────────────────────────────────┐
    │                    JOURNALING DOMAIN                        │
    │                      (Core Domain)                          │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │                   CORE                               │   │
    │  │  • JournalingDomain class                            │   │
    │  │  • Schema definitions                                │   │
    │  │  • Trait management                                  │   │
    │  └─────────────────────────────────────────────────────┘   │
    │                                                             │
    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
    │  │   ENTRY     │ │  ANALYSIS   │ │   PROMPTS   │   ...     │
    │  │  TRACKER    │ │   ENGINE    │ │   SYSTEM    │           │
    │  │             │ │             │ │             │           │
    │  │ • CRUD      │ │ • Emotions  │ │ • Generate  │           │
    │  │ • History   │ │ • Themes    │ │ • Curate    │           │
    │  │ • Search    │ │ • Sentiment │ │ • Personalize│          │
    │  └─────────────┘ └─────────────┘ └─────────────┘           │
    │                                                             │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │                  PATTERNS                            │   │
    │  │  • Mood tracking over time                           │   │
    │  │  • Theme recurrence                                  │   │
    │  │  • Emotional patterns                                │   │
    │  │  • Growth trajectory                                 │   │
    │  └─────────────────────────────────────────────────────┘   │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

Module Structure (Fractal):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
journaling/
├── __init__.py         # Domain registration & exports
├── domain.py           # Main JournalingDomain class
├── schema.py           # Entry schemas & validation
├── tracker/            # Entry tracking sub-module
│   ├── __init__.py
│   ├── entries.py      # Entry CRUD operations
│   ├── history.py      # Historical analysis
│   └── search.py       # Entry search
├── analysis/           # Content analysis sub-module
│   ├── __init__.py
│   ├── emotions.py     # Emotion detection
│   ├── themes.py       # Theme extraction
│   └── sentiment.py    # Sentiment analysis
├── prompts/            # Prompt system sub-module
│   ├── __init__.py
│   ├── generator.py    # AI prompt generation
│   ├── library.py      # Curated prompt library
│   └── personalize.py  # Personalization engine
└── patterns/           # Pattern detection sub-module
    ├── __init__.py
    ├── detector.py     # Pattern detection
    ├── trends.py       # Trend analysis
    └── insights.py     # Insight generation

@module JournalingDomain
"""

# Re-export all public interfaces
from .domain import (
    JournalingDomain,
    JournalingConfig,
    get_journaling_domain,
)
from .schema import (
    JournalingSchema,
    JournalEntry,
    EntryType,
    MoodLevel,
    EmotionCategory,
    EmotionTag,
)
from .tracker import (
    EntryTracker,
    EntryHistory,
    EntrySearch,
    EntryStats,
)
from .analysis import (
    EmotionAnalyzer,
    ThemeExtractor,
    SentimentAnalyzer,
    AnalysisResult,
)
from .prompts import (
    PromptGenerator,
    PromptLibrary,
    PersonalizedPrompt,
)
from .patterns import (
    PatternDetector,
    TrendAnalyzer,
    InsightGenerator,
    JournalingPattern,
    JournalingInsight,
)

__all__ = [
    # Domain
    "JournalingDomain",
    "JournalingConfig",
    "get_journaling_domain",
    # Schema
    "JournalingSchema",
    "JournalEntry",
    "EntryType",
    "MoodLevel",
    "EmotionCategory",
    "EmotionTag",
    # Tracker
    "EntryTracker",
    "EntryHistory",
    "EntrySearch",
    "EntryStats",
    # Analysis
    "EmotionAnalyzer",
    "ThemeExtractor",
    "SentimentAnalyzer",
    "AnalysisResult",
    # Prompts
    "PromptGenerator",
    "PromptLibrary",
    "PersonalizedPrompt",
    # Patterns
    "PatternDetector",
    "TrendAnalyzer",
    "InsightGenerator",
    "JournalingPattern",
    "JournalingInsight",
]
