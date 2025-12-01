"""
Trait Validation - Ensuring Data Integrity

This module provides validation for traits:
- Schema validation (correct types, required fields)
- Value validation (within ranges, valid enums)
- Business rule validation (domain-specific rules)

Validation ensures the Digital Twin maintains data integrity
across all write operations.

@module TraitValidation
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .base import Trait, TraitValueType
from .categories import TraitCategory, ConfidenceThreshold


class ValidationSeverity(str, Enum):
    """Severity of a validation issue."""
    ERROR = "error"       # Cannot proceed
    WARNING = "warning"   # Can proceed with caution
    INFO = "info"         # Informational only


@dataclass
class ValidationError:
    """A single validation issue."""
    code: str
    message: str
    field: Optional[str] = None
    severity: ValidationSeverity = ValidationSeverity.ERROR
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "field": self.field,
            "severity": self.severity.value,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class ValidationResult:
    """Result of validating a trait."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }
    
    def add_error(self, code: str, message: str, field: Optional[str] = None, suggested_fix: Optional[str] = None) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(
            code=code,
            message=message,
            field=field,
            severity=ValidationSeverity.ERROR,
            suggested_fix=suggested_fix,
        ))
        self.is_valid = False
    
    def add_warning(self, code: str, message: str, field: Optional[str] = None, suggested_fix: Optional[str] = None) -> None:
        """Add a validation warning."""
        self.warnings.append(ValidationError(
            code=code,
            message=message,
            field=field,
            severity=ValidationSeverity.WARNING,
            suggested_fix=suggested_fix,
        ))
    
    @classmethod
    def valid(cls) -> "ValidationResult":
        """Create a valid result."""
        return cls(is_valid=True)
    
    @classmethod
    def invalid(cls, code: str, message: str) -> "ValidationResult":
        """Create an invalid result with one error."""
        result = cls(is_valid=False)
        result.add_error(code, message)
        return result


# =============================================================================
# VALIDATION RULES
# =============================================================================

class ValidationRule:
    """Base class for validation rules."""
    
    def validate(self, trait: Trait) -> ValidationResult:
        """Override to implement validation logic."""
        return ValidationResult.valid()


class RequiredFieldsRule(ValidationRule):
    """Validate that required fields are present."""
    
    def validate(self, trait: Trait) -> ValidationResult:
        result = ValidationResult.valid()
        
        if not trait.name:
            result.add_error(
                "MISSING_NAME",
                "Trait name is required",
                field="name",
                suggested_fix="Provide a unique name for the trait"
            )
        
        if not trait.domain:
            result.add_error(
                "MISSING_DOMAIN",
                "Trait domain is required",
                field="domain",
                suggested_fix="Specify which domain this trait belongs to"
            )
        
        if trait.value is None:
            result.add_warning(
                "MISSING_VALUE",
                "Trait has no value",
                field="value",
                suggested_fix="Set a value for the trait"
            )
        
        return result


class ConfidenceRangeRule(ValidationRule):
    """Validate that confidence is within valid range."""
    
    def validate(self, trait: Trait) -> ValidationResult:
        result = ValidationResult.valid()
        
        if trait.confidence < 0.0:
            result.add_error(
                "CONFIDENCE_TOO_LOW",
                f"Confidence cannot be negative: {trait.confidence}",
                field="confidence",
                suggested_fix="Set confidence to a value between 0.0 and 1.0"
            )
        
        if trait.confidence > 1.0:
            result.add_error(
                "CONFIDENCE_TOO_HIGH",
                f"Confidence cannot exceed 1.0: {trait.confidence}",
                field="confidence",
                suggested_fix="Set confidence to a value between 0.0 and 1.0"
            )
        
        if trait.confidence < ConfidenceThreshold.SPECULATION:
            result.add_warning(
                "VERY_LOW_CONFIDENCE",
                f"Confidence is very low ({trait.confidence}), consider not storing",
                field="confidence"
            )
        
        return result


class ValueTypeRule(ValidationRule):
    """Validate that value matches declared type."""
    
    TYPE_CHECKS = {
        TraitValueType.STRING: lambda v: isinstance(v, str),
        TraitValueType.NUMBER: lambda v: isinstance(v, (int, float)),
        TraitValueType.BOOLEAN: lambda v: isinstance(v, bool),
        TraitValueType.LIST: lambda v: isinstance(v, list),
        TraitValueType.OBJECT: lambda v: isinstance(v, dict),
        TraitValueType.SCALE: lambda v: isinstance(v, (int, float)) and 0 <= v <= 1,
    }
    
    def validate(self, trait: Trait) -> ValidationResult:
        result = ValidationResult.valid()
        
        if trait.value is None:
            return result  # None is handled by RequiredFieldsRule
        
        checker = self.TYPE_CHECKS.get(trait.value_type)
        if checker and not checker(trait.value):
            result.add_error(
                "VALUE_TYPE_MISMATCH",
                f"Value type mismatch: expected {trait.value_type.value}, got {type(trait.value).__name__}",
                field="value",
                suggested_fix=f"Ensure value is of type {trait.value_type.value}"
            )
        
        return result


class NameFormatRule(ValidationRule):
    """Validate trait name format."""
    
    def validate(self, trait: Trait) -> ValidationResult:
        result = ValidationResult.valid()
        
        if not trait.name:
            return result  # Handled by RequiredFieldsRule
        
        # Name should be snake_case
        if " " in trait.name:
            result.add_error(
                "INVALID_NAME_FORMAT",
                "Trait name should not contain spaces",
                field="name",
                suggested_fix=f"Use snake_case: {trait.name.replace(' ', '_').lower()}"
            )
        
        if not trait.name.islower() and not trait.name.replace("_", "").islower():
            result.add_warning(
                "NAME_NOT_LOWERCASE",
                "Trait names should be lowercase",
                field="name",
                suggested_fix=f"Use lowercase: {trait.name.lower()}"
            )
        
        return result


class SourceRequiredRule(ValidationRule):
    """Validate that traits have at least one source."""
    
    def validate(self, trait: Trait) -> ValidationResult:
        result = ValidationResult.valid()
        
        if not trait.sources:
            result.add_warning(
                "NO_SOURCES",
                "Trait has no sources - provenance unknown",
                field="sources",
                suggested_fix="Add at least one source for provenance tracking"
            )
        
        return result


# =============================================================================
# TRAIT VALIDATOR
# =============================================================================

class TraitValidator:
    """
    Validates traits against configurable rules.
    
    Usage:
        validator = TraitValidator()
        result = validator.validate(trait)
        if not result.is_valid:
            for error in result.errors:
                print(f"Error: {error.message}")
    """
    
    DEFAULT_RULES = [
        RequiredFieldsRule(),
        ConfidenceRangeRule(),
        ValueTypeRule(),
        NameFormatRule(),
        SourceRequiredRule(),
    ]
    
    def __init__(self, rules: Optional[List[ValidationRule]] = None):
        self.rules = rules or self.DEFAULT_RULES.copy()
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule."""
        self.rules.append(rule)
    
    def validate(self, trait: Trait) -> ValidationResult:
        """
        Validate a trait against all rules.
        
        Returns a ValidationResult with any errors/warnings found.
        """
        final_result = ValidationResult.valid()
        
        for rule in self.rules:
            result = rule.validate(trait)
            
            # Merge errors
            for error in result.errors:
                final_result.errors.append(error)
                final_result.is_valid = False
            
            # Merge warnings
            for warning in result.warnings:
                final_result.warnings.append(warning)
        
        return final_result
    
    def validate_many(self, traits: List[Trait]) -> Dict[str, ValidationResult]:
        """Validate multiple traits, return results keyed by trait path."""
        return {trait.path: self.validate(trait) for trait in traits}


# =============================================================================
# DOMAIN-SPECIFIC VALIDATORS
# =============================================================================

class GenesisTraitValidator(TraitValidator):
    """Validator with Genesis-specific rules."""
    
    def __init__(self):
        super().__init__()
        # Add Genesis-specific rules here if needed


class HealthTraitValidator(TraitValidator):
    """Validator with health-specific rules."""
    
    def __init__(self):
        super().__init__()
        # Add health-specific rules here if needed
