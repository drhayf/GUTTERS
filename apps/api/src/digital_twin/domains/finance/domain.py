"""
Finance Domain - Main Domain Class

This module contains the main FinanceDomain class that orchestrates
all finance functionality and integrates with the Digital Twin.

@module FinanceDomain
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
import logging

from ..base import BaseDomain, DomainSchema, TraitSchema
from ..registry import DomainRegistry
from ..core_types import (
    DomainType,
    DomainCapability,
    DomainMetadata,
    OptionalDomainId,
)
from ...traits import TraitCategory, TraitFramework

from .schema import (
    Transaction,
    FinancialGoal,
    FinanceSchema,
    TransactionType,
    SpendingCategory,
    FinancialGoalType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# FINANCE CONFIG
# =============================================================================

@dataclass
class FinanceConfig:
    """
    Configuration for the Finance domain.
    """
    # Feature toggles
    enable_auto_categorization: bool = True
    enable_pattern_detection: bool = True
    enable_budget_alerts: bool = True
    enable_goal_projections: bool = True
    
    # Analysis settings
    pattern_detection_days: int = 90
    
    # Budget settings
    budget_warning_threshold: float = 0.8  # Alert at 80% of budget
    
    # Currency
    default_currency: str = "USD"
    
    # Privacy
    share_with_agents: bool = True
    anonymize_exports: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_auto_categorization": self.enable_auto_categorization,
            "enable_pattern_detection": self.enable_pattern_detection,
            "enable_budget_alerts": self.enable_budget_alerts,
            "enable_goal_projections": self.enable_goal_projections,
            "pattern_detection_days": self.pattern_detection_days,
            "budget_warning_threshold": self.budget_warning_threshold,
            "default_currency": self.default_currency,
            "share_with_agents": self.share_with_agents,
            "anonymize_exports": self.anonymize_exports,
        }


# =============================================================================
# FINANCE DOMAIN
# =============================================================================

@DomainRegistry.register
class FinanceDomain(BaseDomain):
    """
    Finance Domain - Optional Domain for financial tracking and insights.
    
    This is an OPTIONAL DOMAIN that provides:
    - Transaction logging and categorization
    - Budget management
    - Spending analytics
    - Financial goal tracking
    - Wealth building insights
    """
    
    # -------------------------------------------------------------------------
    # Domain Identity
    # -------------------------------------------------------------------------
    
    domain_id = OptionalDomainId.FINANCE
    display_name = "Finance"
    description = "Financial tracking, budgeting, and wealth insights"
    icon = "💰"
    version = "1.0.0"
    priority = 70  # Standard priority
    
    # Classification
    domain_type = DomainType.OPTIONAL
    is_core = False  # Can be disabled
    
    # Capabilities this domain provides
    capabilities = {
        DomainCapability.READ_TRAITS,
        DomainCapability.WRITE_TRAITS,
        DomainCapability.DETECT_PATTERNS,
        DomainCapability.GENERATE_INSIGHTS,
        DomainCapability.CALCULATE,
    }
    
    # Sub-domain IDs
    sub_domain_ids = [
        "budgeting",     # Budget creation and tracking
        "spending",      # Spending analytics
        "investing",     # Investment tracking
        "bills",         # Recurring bills and subscriptions
        "goals",         # Financial goals
    ]
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def __init__(self, config: Optional[FinanceConfig] = None):
        """Initialize the Finance domain."""
        self.config = config or FinanceConfig()
        
        # In-memory caches (for scaffold - real impl uses persistence)
        self._transactions: Dict[str, Transaction] = {}
        self._goals: Dict[str, FinancialGoal] = {}
        
        # Sub-module instances (lazy loaded)
        self._tracker = None
        self._budget_manager = None
        self._goal_manager = None
        self._pattern_detector = None
        
        logger.info(f"FinanceDomain initialized with config: {self.config.to_dict()}")
    
    # -------------------------------------------------------------------------
    # Schema Implementation (Required by BaseDomain)
    # -------------------------------------------------------------------------
    
    def get_schema(self) -> DomainSchema:
        """Get the domain schema with all trait definitions."""
        schema = DomainSchema(domain_id=self.domain_id)
        
        for trait_key, trait_def in FinanceSchema.TRAITS.items():
            schema.add_trait(TraitSchema(
                name=trait_key,
                display_name=trait_def["name"],
                description=trait_def["description"],
                value_type=trait_def.get("value_type", "string"),
                category=TraitCategory.DETECTED,
                frameworks=[TraitFramework.BEHAVIORAL_PATTERNS],
            ))
        
        return schema
    
    # -------------------------------------------------------------------------
    # Transaction Operations
    # -------------------------------------------------------------------------
    
    async def log_transaction(
        self,
        amount: Decimal,
        transaction_type: TransactionType = TransactionType.EXPENSE,
        category: SpendingCategory = SpendingCategory.OTHER,
        description: str = "",
        merchant: Optional[str] = None,
        tags: Optional[List[str]] = None,
        transaction_date: Optional[date] = None,
    ) -> Transaction:
        """Log a financial transaction."""
        transaction = Transaction(
            transaction_type=transaction_type,
            amount=amount,
            category=category,
            description=description,
            merchant=merchant,
            tags=tags or [],
            transaction_date=transaction_date or date.today(),
        )
        
        self._transactions[transaction.transaction_id] = transaction
        
        return transaction
    
    async def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Retrieve a transaction by ID."""
        return self._transactions.get(transaction_id)
    
    async def list_transactions(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[SpendingCategory] = None,
        transaction_type: Optional[TransactionType] = None,
        limit: int = 100,
    ) -> List[Transaction]:
        """List transactions with optional filters."""
        transactions = list(self._transactions.values())
        
        if category:
            transactions = [t for t in transactions if t.category == category]
        
        if transaction_type:
            transactions = [t for t in transactions if t.transaction_type == transaction_type]
        
        if start_date:
            transactions = [t for t in transactions if t.transaction_date >= start_date]
        
        if end_date:
            transactions = [t for t in transactions if t.transaction_date <= end_date]
        
        transactions.sort(key=lambda t: t.transaction_date, reverse=True)
        
        return transactions[:limit]
    
    # -------------------------------------------------------------------------
    # Goal Operations
    # -------------------------------------------------------------------------
    
    async def create_goal(
        self,
        name: str,
        target_amount: Decimal,
        goal_type: FinancialGoalType = FinancialGoalType.SAVINGS,
        target_date: Optional[date] = None,
    ) -> FinancialGoal:
        """Create a financial goal."""
        goal = FinancialGoal(
            goal_type=goal_type,
            name=name,
            target_amount=target_amount,
            target_date=target_date,
        )
        
        self._goals[goal.goal_id] = goal
        
        return goal
    
    async def get_goal(self, goal_id: str) -> Optional[FinancialGoal]:
        """Retrieve a goal by ID."""
        return self._goals.get(goal_id)
    
    async def list_goals(self, active_only: bool = True) -> List[FinancialGoal]:
        """List financial goals."""
        goals = list(self._goals.values())
        
        if active_only:
            goals = [g for g in goals if g.is_active]
        
        return goals
    
    # -------------------------------------------------------------------------
    # Domain Metadata
    # -------------------------------------------------------------------------
    
    @property
    def metadata(self) -> DomainMetadata:
        """Get domain metadata."""
        return DomainMetadata(
            domain_id=self.domain_id,
            display_name=self.display_name,
            description=self.description,
            domain_type=self.domain_type,
            icon=self.icon,
            version=self.version,
            priority=self.priority,
            capabilities=self.capabilities,
            sub_domain_ids=self.sub_domain_ids,
            is_core=self.is_core,
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

_domain_instance: Optional[FinanceDomain] = None


def get_finance_domain(config: Optional[FinanceConfig] = None) -> FinanceDomain:
    """Get or create the Finance domain singleton."""
    global _domain_instance
    
    if _domain_instance is None:
        _domain_instance = FinanceDomain(config=config)
    
    return _domain_instance
