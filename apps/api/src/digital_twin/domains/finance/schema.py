"""
Finance Schema - Data Types and Trait Definitions

This module defines all data structures and trait schemas for the
Finance domain. These are the "nouns" of the finance system.

Key Types:
- Transaction: A single financial transaction
- FinancialGoal: A financial goal with progress tracking
- Budget: A budget category with limits

@module FinanceSchema
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from uuid import uuid4


# =============================================================================
# ENUMS - Transaction and category classification
# =============================================================================

class TransactionType(str, Enum):
    """Types of financial transactions."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    INVESTMENT = "investment"
    REFUND = "refund"


class SpendingCategory(str, Enum):
    """Primary spending categories."""
    HOUSING = "housing"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    PERSONAL = "personal"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    EDUCATION = "education"
    SAVINGS = "savings"
    INVESTMENTS = "investments"
    DEBT = "debt"
    GIFTS = "gifts"
    OTHER = "other"


class IncomeSource(str, Enum):
    """Types of income sources."""
    SALARY = "salary"
    FREELANCE = "freelance"
    BUSINESS = "business"
    INVESTMENTS = "investments"
    RENTAL = "rental"
    SIDE_HUSTLE = "side_hustle"
    GIFTS = "gifts"
    OTHER = "other"


class FinancialGoalType(str, Enum):
    """Types of financial goals."""
    EMERGENCY_FUND = "emergency_fund"
    DEBT_PAYOFF = "debt_payoff"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    RETIREMENT = "retirement"
    MAJOR_PURCHASE = "major_purchase"
    TRAVEL = "travel"
    EDUCATION = "education"


class RiskTolerance(str, Enum):
    """Investment risk tolerance levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


# =============================================================================
# DATA CLASSES - Transaction and goal structures
# =============================================================================

@dataclass
class Transaction:
    """A single financial transaction."""
    transaction_id: str = field(default_factory=lambda: str(uuid4()))
    transaction_type: TransactionType = TransactionType.EXPENSE
    amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    
    # Categorization
    category: SpendingCategory = SpendingCategory.OTHER
    subcategory: Optional[str] = None
    
    # Details
    description: str = ""
    merchant: Optional[str] = None
    
    # Timestamps
    transaction_date: date = field(default_factory=date.today)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Source
    account_id: Optional[str] = None
    source: str = "manual"  # "manual", "import", "api", "recurring"
    
    # Tags and notes
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    # Recurring
    is_recurring: bool = False
    recurring_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type.value,
            "amount": str(self.amount),
            "currency": self.currency,
            "category": self.category.value,
            "subcategory": self.subcategory,
            "description": self.description,
            "merchant": self.merchant,
            "transaction_date": self.transaction_date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "account_id": self.account_id,
            "source": self.source,
            "tags": self.tags,
            "notes": self.notes,
            "is_recurring": self.is_recurring,
            "recurring_id": self.recurring_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transaction":
        return cls(
            transaction_id=data.get("transaction_id", str(uuid4())),
            transaction_type=TransactionType(data.get("transaction_type", "expense")),
            amount=Decimal(data.get("amount", "0.00")),
            currency=data.get("currency", "USD"),
            category=SpendingCategory(data.get("category", "other")),
            subcategory=data.get("subcategory"),
            description=data.get("description", ""),
            merchant=data.get("merchant"),
            transaction_date=date.fromisoformat(data["transaction_date"]) if "transaction_date" in data else date.today(),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            account_id=data.get("account_id"),
            source=data.get("source", "manual"),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            is_recurring=data.get("is_recurring", False),
            recurring_id=data.get("recurring_id"),
        )


@dataclass
class FinancialGoal:
    """A financial goal being tracked."""
    goal_id: str = field(default_factory=lambda: str(uuid4()))
    goal_type: FinancialGoalType = FinancialGoalType.SAVINGS
    name: str = ""
    target_amount: Decimal = Decimal("0.00")
    current_amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    
    # Timeline
    start_date: date = field(default_factory=date.today)
    target_date: Optional[date] = None
    
    # Status
    is_active: bool = True
    is_completed: bool = False
    completed_date: Optional[date] = None
    
    # Tracking
    contribution_frequency: str = "monthly"  # daily, weekly, monthly
    auto_contribute: bool = False
    
    @property
    def progress_percentage(self) -> float:
        """Calculate goal progress percentage."""
        if self.target_amount == 0:
            return 0.0
        return float(self.current_amount / self.target_amount * 100)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "goal_id": self.goal_id,
            "goal_type": self.goal_type.value,
            "name": self.name,
            "target_amount": str(self.target_amount),
            "current_amount": str(self.current_amount),
            "currency": self.currency,
            "start_date": self.start_date.isoformat(),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "progress_percentage": self.progress_percentage,
            "contribution_frequency": self.contribution_frequency,
            "auto_contribute": self.auto_contribute,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinancialGoal":
        return cls(
            goal_id=data.get("goal_id", str(uuid4())),
            goal_type=FinancialGoalType(data.get("goal_type", "savings")),
            name=data.get("name", ""),
            target_amount=Decimal(data.get("target_amount", "0.00")),
            current_amount=Decimal(data.get("current_amount", "0.00")),
            currency=data.get("currency", "USD"),
            start_date=date.fromisoformat(data["start_date"]) if "start_date" in data else date.today(),
            target_date=date.fromisoformat(data["target_date"]) if data.get("target_date") else None,
            is_active=data.get("is_active", True),
            is_completed=data.get("is_completed", False),
            completed_date=date.fromisoformat(data["completed_date"]) if data.get("completed_date") else None,
            contribution_frequency=data.get("contribution_frequency", "monthly"),
            auto_contribute=data.get("auto_contribute", False),
        )


# =============================================================================
# FINANCE SCHEMA - Master schema definition
# =============================================================================

class FinanceSchema:
    """
    Schema definitions for the Finance domain.
    
    Provides trait schemas and validation rules.
    """
    
    TRAITS = {
        # Spending patterns
        "spending_style": {
            "name": "Spending Style",
            "description": "User's general approach to spending",
            "value_type": "string",
            "possible_values": ["frugal", "balanced", "generous", "impulsive"],
        },
        "primary_spending_categories": {
            "name": "Primary Spending Categories",
            "description": "Categories where user spends the most",
            "value_type": "list",
            "item_type": "string",
        },
        "monthly_spending_average": {
            "name": "Monthly Spending Average",
            "description": "Average monthly expenditure",
            "value_type": "float",
            "unit": "currency",
        },
        
        # Income patterns
        "primary_income_source": {
            "name": "Primary Income Source",
            "description": "User's main source of income",
            "value_type": "string",
            "possible_values": [s.value for s in IncomeSource],
        },
        "income_stability": {
            "name": "Income Stability",
            "description": "How stable/predictable income is (1-10)",
            "value_type": "float",
            "min_value": 1.0,
            "max_value": 10.0,
        },
        
        # Financial behavior
        "savings_rate": {
            "name": "Savings Rate",
            "description": "Percentage of income saved",
            "value_type": "float",
            "min_value": 0.0,
            "max_value": 100.0,
            "unit": "percent",
        },
        "risk_tolerance": {
            "name": "Risk Tolerance",
            "description": "Investment risk tolerance level",
            "value_type": "string",
            "possible_values": [r.value for r in RiskTolerance],
        },
        "budgeting_adherence": {
            "name": "Budgeting Adherence",
            "description": "How well user sticks to budgets (1-10)",
            "value_type": "float",
            "min_value": 1.0,
            "max_value": 10.0,
        },
        
        # Financial goals
        "active_goal_types": {
            "name": "Active Goal Types",
            "description": "Types of financial goals user is pursuing",
            "value_type": "list",
            "item_type": "string",
        },
        "financial_priority": {
            "name": "Financial Priority",
            "description": "User's top financial priority",
            "value_type": "string",
            "possible_values": ["debt_freedom", "wealth_building", "security", "experiences", "balance"],
        },
        
        # Stress and relationship with money
        "financial_stress_level": {
            "name": "Financial Stress Level",
            "description": "Current level of financial stress (1-10)",
            "value_type": "float",
            "min_value": 1.0,
            "max_value": 10.0,
        },
        "money_mindset": {
            "name": "Money Mindset",
            "description": "User's general relationship with money",
            "value_type": "string",
            "possible_values": ["abundance", "scarcity", "neutral", "anxious", "confident"],
        },
    }
    
    @classmethod
    def get_trait_schema(cls, trait_key: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific trait."""
        return cls.TRAITS.get(trait_key)
    
    @classmethod
    def list_traits(cls) -> List[str]:
        """List all trait keys."""
        return list(cls.TRAITS.keys())
