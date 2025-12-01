"""
Finance Tracker - Transaction Tracking and Analytics

This sub-module handles all transaction operations:
- Transaction CRUD
- Auto-categorization
- Spending analytics

@module FinanceTracker
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
import logging

from ..schema import Transaction, TransactionType, SpendingCategory

logger = logging.getLogger(__name__)


# =============================================================================
# TRANSACTION TRACKER
# =============================================================================

class TransactionTracker:
    """
    Tracks and manages financial transactions.
    
    SCAFFOLD: Basic in-memory implementation.
    """
    
    def __init__(self):
        self._transactions: Dict[str, Transaction] = {}
    
    async def create(self, transaction: Transaction) -> Transaction:
        """Create a new transaction."""
        self._transactions[transaction.transaction_id] = transaction
        return transaction
    
    async def get(self, transaction_id: str) -> Optional[Transaction]:
        """Get a transaction by ID."""
        return self._transactions.get(transaction_id)
    
    async def update(self, transaction: Transaction) -> Transaction:
        """Update an existing transaction."""
        self._transactions[transaction.transaction_id] = transaction
        return transaction
    
    async def delete(self, transaction_id: str) -> bool:
        """Delete a transaction."""
        if transaction_id in self._transactions:
            del self._transactions[transaction_id]
            return True
        return False
    
    async def list_all(self, limit: int = 100) -> List[Transaction]:
        """List all transactions."""
        transactions = list(self._transactions.values())
        transactions.sort(key=lambda t: t.transaction_date, reverse=True)
        return transactions[:limit]


# =============================================================================
# TRANSACTION CATEGORIZER
# =============================================================================

class TransactionCategorizer:
    """
    Auto-categorizes transactions based on merchant and description.
    
    SCAFFOLD: Basic keyword matching.
    Full implementation will use ML for smart categorization.
    """
    
    MERCHANT_CATEGORIES = {
        "uber": SpendingCategory.TRANSPORTATION,
        "lyft": SpendingCategory.TRANSPORTATION,
        "starbucks": SpendingCategory.FOOD,
        "amazon": SpendingCategory.SHOPPING,
        "netflix": SpendingCategory.ENTERTAINMENT,
        "spotify": SpendingCategory.ENTERTAINMENT,
        "whole foods": SpendingCategory.FOOD,
        "cvs": SpendingCategory.HEALTHCARE,
        "walgreens": SpendingCategory.HEALTHCARE,
    }
    
    async def categorize(self, transaction: Transaction) -> SpendingCategory:
        """Auto-categorize a transaction."""
        # Check merchant first
        if transaction.merchant:
            merchant_lower = transaction.merchant.lower()
            for keyword, category in self.MERCHANT_CATEGORIES.items():
                if keyword in merchant_lower:
                    return category
        
        # Check description
        if transaction.description:
            desc_lower = transaction.description.lower()
            for keyword, category in self.MERCHANT_CATEGORIES.items():
                if keyword in desc_lower:
                    return category
        
        return transaction.category or SpendingCategory.OTHER


# =============================================================================
# SPENDING ANALYTICS
# =============================================================================

@dataclass
class SpendingSummary:
    """Summary of spending for a period."""
    total_spent: Decimal = Decimal("0.00")
    total_income: Decimal = Decimal("0.00")
    net_flow: Decimal = Decimal("0.00")
    by_category: Dict[str, Decimal] = field(default_factory=dict)
    transaction_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_spent": str(self.total_spent),
            "total_income": str(self.total_income),
            "net_flow": str(self.net_flow),
            "by_category": {k: str(v) for k, v in self.by_category.items()},
            "transaction_count": self.transaction_count,
        }


class SpendingAnalytics:
    """
    Analyzes spending patterns.
    
    SCAFFOLD: Basic aggregation.
    """
    
    def __init__(self, tracker: TransactionTracker):
        self._tracker = tracker
    
    async def get_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> SpendingSummary:
        """Get spending summary for a period."""
        transactions = await self._tracker.list_all(limit=1000)
        
        # Filter by date
        if start_date:
            transactions = [t for t in transactions if t.transaction_date >= start_date]
        if end_date:
            transactions = [t for t in transactions if t.transaction_date <= end_date]
        
        total_spent = Decimal("0.00")
        total_income = Decimal("0.00")
        by_category: Dict[str, Decimal] = {}
        
        for t in transactions:
            if t.transaction_type == TransactionType.EXPENSE:
                total_spent += t.amount
                cat = t.category.value
                by_category[cat] = by_category.get(cat, Decimal("0.00")) + t.amount
            elif t.transaction_type == TransactionType.INCOME:
                total_income += t.amount
        
        return SpendingSummary(
            total_spent=total_spent,
            total_income=total_income,
            net_flow=total_income - total_spent,
            by_category=by_category,
            transaction_count=len(transactions),
        )


__all__ = [
    "TransactionTracker",
    "TransactionCategorizer",
    "SpendingAnalytics",
    "SpendingSummary",
]
