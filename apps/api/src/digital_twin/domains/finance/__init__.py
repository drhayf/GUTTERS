"""
Finance Domain - Optional Domain for Financial Tracking and Insights

The Finance domain is an OPTIONAL DOMAIN that provides:
- Transaction logging and categorization
- Budget management
- Spending analytics
- Financial goal tracking
- Wealth building insights

This domain follows the Fractal Extensibility Pattern.

Architecture:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ┌─────────────────────────────────────────────────────────────┐
    │                     FINANCE DOMAIN                          │
    │                    (Optional Domain)                        │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │                   CORE                               │   │
    │  │  • FinanceDomain class                               │   │
    │  │  • Schema definitions                                │   │
    │  │  • Trait management                                  │   │
    │  └─────────────────────────────────────────────────────┘   │
    │                                                             │
    │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
    │  │ TRANSACTION │ │   BUDGET    │ │   GOALS     │   ...     │
    │  │  TRACKER    │ │   MANAGER   │ │  TRACKER    │           │
    │  │             │ │             │ │             │           │
    │  │ • CRUD      │ │ • Create    │ │ • Create    │           │
    │  │ • Categorize│ │ • Track     │ │ • Progress  │           │
    │  │ • Analytics │ │ • Alerts    │ │ • Insights  │           │
    │  └─────────────┘ └─────────────┘ └─────────────┘           │
    │                                                             │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │                  PATTERNS                            │   │
    │  │  • Spending patterns                                 │   │
    │  │  • Income patterns                                   │   │
    │  │  • Savings behavior                                  │   │
    │  │  • Risk profile                                      │   │
    │  └─────────────────────────────────────────────────────┘   │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

Module Structure (Fractal):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
finance/
├── __init__.py         # Domain registration & exports
├── domain.py           # Main FinanceDomain class
├── schema.py           # Transaction/goal schemas & validation
├── tracker/            # Transaction tracking sub-module
│   ├── __init__.py
│   ├── transactions.py # Transaction CRUD
│   ├── categorizer.py  # Auto-categorization
│   └── analytics.py    # Spending analytics
├── budget/             # Budget management sub-module
│   ├── __init__.py
│   ├── manager.py      # Budget CRUD
│   ├── tracker.py      # Budget progress
│   └── alerts.py       # Budget alerts
├── goals/              # Financial goals sub-module
│   ├── __init__.py
│   ├── manager.py      # Goal CRUD
│   ├── progress.py     # Progress tracking
│   └── projections.py  # Goal projections
└── patterns/           # Pattern detection sub-module
    ├── __init__.py
    ├── detector.py     # Pattern detection
    ├── trends.py       # Trend analysis
    └── insights.py     # Insight generation

@module FinanceDomain
"""

# Re-export all public interfaces
from .domain import (
    FinanceDomain,
    FinanceConfig,
    get_finance_domain,
)
from .schema import (
    FinanceSchema,
    Transaction,
    TransactionType,
    SpendingCategory,
    IncomeSource,
    FinancialGoal,
    FinancialGoalType,
    RiskTolerance,
)
from .tracker import (
    TransactionTracker,
    TransactionCategorizer,
    SpendingAnalytics,
)
from .budget import (
    Budget,
    BudgetManager,
    BudgetTracker,
    BudgetAlert,
)
from .goals import (
    GoalManager,
    GoalProgress,
    GoalProjection,
)
from .patterns import (
    PatternType,
    TrendDirection,
    PatternDetector,
    TrendAnalyzer,
    InsightGenerator,
    FinancialPattern,
    FinancialTrend,
    FinancialInsight,
)

__all__ = [
    # Domain
    "FinanceDomain",
    "FinanceConfig",
    "get_finance_domain",
    # Schema
    "FinanceSchema",
    "Transaction",
    "TransactionType",
    "SpendingCategory",
    "IncomeSource",
    "FinancialGoal",
    "FinancialGoalType",
    "RiskTolerance",
    # Tracker
    "TransactionTracker",
    "TransactionCategorizer",
    "SpendingAnalytics",
    # Budget
    "Budget",
    "BudgetManager",
    "BudgetTracker",
    "BudgetAlert",
    # Goals
    "GoalManager",
    "GoalProgress",
    "GoalProjection",
    # Patterns
    "PatternType",
    "TrendDirection",
    "PatternDetector",
    "TrendAnalyzer",
    "InsightGenerator",
    "FinancialPattern",
    "FinancialTrend",
    "FinancialInsight",
]
