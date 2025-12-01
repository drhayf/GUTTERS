"""
Finance Budget - Budget Management

This sub-module handles budget operations:
- Budget creation and tracking
- Budget alerts
- Progress monitoring

@module FinanceBudget
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from uuid import uuid4
import logging

from ..schema import SpendingCategory

logger = logging.getLogger(__name__)


# =============================================================================
# BUDGET DATA STRUCTURES
# =============================================================================

@dataclass
class Budget:
    """A budget for a spending category."""
    budget_id: str = field(default_factory=lambda: str(uuid4()))
    category: SpendingCategory = SpendingCategory.OTHER
    name: str = ""
    amount: Decimal = Decimal("0.00")
    spent: Decimal = Decimal("0.00")
    period: str = "monthly"  # weekly, monthly, yearly
    start_date: date = field(default_factory=date.today)
    
    @property
    def remaining(self) -> Decimal:
        return self.amount - self.spent
    
    @property
    def percentage_used(self) -> float:
        if self.amount == 0:
            return 0.0
        return float(self.spent / self.amount * 100)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "budget_id": self.budget_id,
            "category": self.category.value,
            "name": self.name,
            "amount": str(self.amount),
            "spent": str(self.spent),
            "remaining": str(self.remaining),
            "percentage_used": self.percentage_used,
            "period": self.period,
            "start_date": self.start_date.isoformat(),
        }


@dataclass
class BudgetAlert:
    """An alert for budget status."""
    alert_id: str = field(default_factory=lambda: str(uuid4()))
    budget_id: str = ""
    alert_type: str = ""  # warning, exceeded, on_track
    message: str = ""
    percentage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "budget_id": self.budget_id,
            "alert_type": self.alert_type,
            "message": self.message,
            "percentage": self.percentage,
        }


# =============================================================================
# BUDGET MANAGER
# =============================================================================

class BudgetManager:
    """
    Manages budgets.
    
    SCAFFOLD: Basic in-memory implementation.
    """
    
    def __init__(self):
        self._budgets: Dict[str, Budget] = {}
    
    async def create(self, budget: Budget) -> Budget:
        """Create a new budget."""
        self._budgets[budget.budget_id] = budget
        return budget
    
    async def get(self, budget_id: str) -> Optional[Budget]:
        """Get a budget by ID."""
        return self._budgets.get(budget_id)
    
    async def update(self, budget: Budget) -> Budget:
        """Update a budget."""
        self._budgets[budget.budget_id] = budget
        return budget
    
    async def delete(self, budget_id: str) -> bool:
        """Delete a budget."""
        if budget_id in self._budgets:
            del self._budgets[budget_id]
            return True
        return False
    
    async def list_all(self) -> List[Budget]:
        """List all budgets."""
        return list(self._budgets.values())


# =============================================================================
# BUDGET TRACKER
# =============================================================================

class BudgetTracker:
    """
    Tracks budget progress.
    
    SCAFFOLD: Basic tracking.
    """
    
    def __init__(self, manager: BudgetManager):
        self._manager = manager
    
    async def update_spending(
        self,
        category: SpendingCategory,
        amount: Decimal,
    ) -> Optional[Budget]:
        """Update spending for a category."""
        budgets = await self._manager.list_all()
        
        for budget in budgets:
            if budget.category == category:
                budget.spent += amount
                await self._manager.update(budget)
                return budget
        
        return None
    
    async def check_alerts(self, threshold: float = 0.8) -> List[BudgetAlert]:
        """Check all budgets for alerts."""
        alerts = []
        budgets = await self._manager.list_all()
        
        for budget in budgets:
            percentage = budget.percentage_used / 100
            
            if percentage >= 1.0:
                alerts.append(BudgetAlert(
                    budget_id=budget.budget_id,
                    alert_type="exceeded",
                    message=f"Budget for {budget.category.value} exceeded!",
                    percentage=percentage * 100,
                ))
            elif percentage >= threshold:
                alerts.append(BudgetAlert(
                    budget_id=budget.budget_id,
                    alert_type="warning",
                    message=f"Budget for {budget.category.value} is {percentage*100:.0f}% used",
                    percentage=percentage * 100,
                ))
        
        return alerts


__all__ = [
    "Budget",
    "BudgetAlert",
    "BudgetManager",
    "BudgetTracker",
]
