"""
Calculation Module Registry - Self-Registering Plugin System

Each calculation module registers itself using @CalculationModuleRegistry.register
decorator. The onboarding flow queries this registry to determine which modules
to run, how to display progress, and what order to execute them in.

Example:
    @CalculationModuleRegistry.register(
        name="astrology",
        display_name="Astrology",
        description="Calculating natal chart..."
    )
    class AstrologyCalculator:
        async def calculate(self, **kwargs):
            ...
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModuleMetadata:
    """
    Metadata for a registered calculation module.

    Attributes:
        name: Internal identifier (e.g., "astrology")
        display_name: Human-readable name (e.g., "Astrology")
        description: Short description for progress UI
        calculator_class: The calculator class to instantiate
        weight: Relative calculation time (for progress bars)
        requires_birth_time: Whether exact birth time is needed
        order: Execution order (lower runs first)
        enabled: Whether module is active
        version: Module version for compatibility tracking
    """

    name: str
    display_name: str
    description: str
    calculator_class: type
    weight: int = 1
    requires_birth_time: bool = True
    order: int = 100
    enabled: bool = True
    version: str = "1.0.0"


class CalculationModuleRegistry:
    """
    Central registry for all calculation modules.

    Usage:
        # In calculator file:
        @CalculationModuleRegistry.register(name="astrology", ...)
        class AstrologyCalculator:
            async def calculate(self, birth_date, birth_time, ...):
                ...

        # In API:
        modules = CalculationModuleRegistry.get_enabled_modules()
        results = await CalculationModuleRegistry.calculate_all(user, db)
    """

    _modules: Dict[str, ModuleMetadata] = {}
    _initialized: bool = False

    @classmethod
    def register(
        cls,
        name: str,
        display_name: str,
        description: str,
        weight: int = 1,
        requires_birth_time: bool = True,
        order: int = 100,
        version: str = "1.0.0",
        enabled: bool = True,
    ):
        """
        Decorator to register a calculation module.

        Args:
            name: Unique module identifier
            display_name: Name shown in UI
            description: Progress message (e.g., "Calculating natal chart...")
            weight: Relative time weight (1 = standard, 2 = twice as long)
            requires_birth_time: If False, runs even with unknown time
            order: Execution order (lower = earlier)
            version: Module version
            enabled: Whether module is active

        Returns:
            Decorator function
        """

        def decorator(calculator_class):
            if name in cls._modules:
                logger.warning(f"Module '{name}' already registered, overwriting")

            cls._modules[name] = ModuleMetadata(
                name=name,
                display_name=display_name,
                description=description,
                calculator_class=calculator_class,
                weight=weight,
                requires_birth_time=requires_birth_time,
                order=order,
                enabled=enabled,
                version=version,
            )

            logger.info(f"Registered calculation module: {name} (v{version})")
            return calculator_class

        return decorator

    @classmethod
    def get_all_modules(cls) -> Dict[str, ModuleMetadata]:
        """Get all registered modules (including disabled)."""
        cls._ensure_modules_loaded()
        return cls._modules.copy()

    @classmethod
    def get_enabled_modules(cls) -> Dict[str, ModuleMetadata]:
        """Get only enabled modules, sorted by execution order."""
        cls._ensure_modules_loaded()
        modules = {k: v for k, v in cls._modules.items() if v.enabled}
        # Sort by order
        sorted_modules = dict(sorted(modules.items(), key=lambda x: x[1].order))
        return sorted_modules

    @classmethod
    def get_module(cls, name: str) -> Optional[ModuleMetadata]:
        """Get specific module by name."""
        cls._ensure_modules_loaded()
        return cls._modules.get(name)

    @classmethod
    def get_modules_for_birth_data(cls, has_birth_time: bool) -> Dict[str, ModuleMetadata]:
        """
        Get modules that can be calculated with available birth data.

        If birth time is unknown, only returns modules that don't require it.
        """
        modules = cls.get_enabled_modules()

        # We now run ALL enabled modules, even if birth time is unknown.
        # Calculators are responsible for handling missing time via probabilistic/solar chart logic.
        return modules

    @classmethod
    def get_total_weight(cls, has_birth_time: bool = True) -> int:
        """
        Calculate total weight for progress calculation.

        Only counts modules that will actually run based on birth data.
        """
        modules = cls.get_modules_for_birth_data(has_birth_time)
        return sum(m.weight for m in modules.values())

    @classmethod
    async def calculate_all(cls, user, db_session, has_birth_time: bool = True) -> Dict[str, Any]:
        """
        Run all enabled calculators in order.

        Args:
            user: User model instance with birth data
            db_session: Database session
            has_birth_time: Whether birth time is known

        Returns:
            Dict mapping module name to calculation result.
            Errors are captured as {"error": "message"} within results.
        """
        modules = cls.get_modules_for_birth_data(has_birth_time)
        results = {}

        logger.info(f"Calculating {len(modules)} modules for user {user.id}")

        for name, metadata in modules.items():
            try:
                logger.debug(f"Calculating module: {name}")

                # Instantiate calculator
                calculator = metadata.calculator_class()

                # Prepare kwargs (calculators may need different args)
                # Some calculators might only accept specific args, or check for them.
                # Since we standardized on specific calculator classes, we'll pass standard fields.
                # Note: The calculators might be using different signatures or **kwargs,
                # we'll assume they are reasonably robust or we'll wrap/adjust.
                kwargs = {
                    "name": user.name,
                    "birth_date": user.birth_date,
                    "birth_time": user.birth_time,
                    "birth_location": user.birth_location,
                    "latitude": user.birth_latitude,
                    "longitude": user.birth_longitude,
                    "timezone": getattr(user, "timezone", "UTC"),
                }

                # Call calculate method
                # We assume the calculator class follows a synchronous-compatible interface pattern we established
                # or is async. The plan implies `async def calculate`.
                result = await calculator.calculate(**kwargs)
                results[name] = result

                logger.info(f"Module {name} calculated successfully")

            except Exception as e:
                logger.error(f"Error calculating {name}: {e}", exc_info=True)
                results[name] = {"error": str(e), "module": name, "timestamp": datetime.utcnow().isoformat()}

        return results

    @classmethod
    def get_registry_metadata(cls, has_birth_time: bool = True) -> Dict[str, Any]:
        """
        Get registry metadata for frontend.

        Returns module list with progress weights, display info,
        and cumulative progress percentages.

        Frontend uses this to:
        - Display module names during calculation
        - Show accurate progress bars
        - Handle unknown birth time gracefully
        """
        modules = cls.get_modules_for_birth_data(has_birth_time)
        total_weight = cls.get_total_weight(has_birth_time)

        cumulative_progress = 0
        module_list = []

        for metadata in modules.values():
            # Calculate this module's contribution to total progress
            module_percentage = (metadata.weight / total_weight) * 100 if total_weight > 0 else 0

            module_list.append(
                {
                    "name": metadata.name,
                    "display_name": metadata.display_name,
                    "description": metadata.description,
                    "weight": metadata.weight,
                    "progress_percentage": module_percentage,
                    "cumulative_progress_start": cumulative_progress,
                    "cumulative_progress_end": cumulative_progress + module_percentage,
                    "requires_birth_time": metadata.requires_birth_time,
                    "order": metadata.order,
                    "version": metadata.version,
                }
            )

            cumulative_progress += module_percentage

        return {
            "modules": module_list,
            "total_modules": len(modules),
            "total_weight": total_weight,
            "has_birth_time": has_birth_time,
        }

    @classmethod
    def _ensure_modules_loaded(cls):
        """
        Ensure all module files have been imported.

        This is called lazily to guarantee all @register decorators
        have executed before querying the registry.
        """
        if not cls._initialized:
            # Import all calculator modules to trigger registration
            try:
                # We use importlib or direct imports. Since the structure is fixed, direct is safer for static analysis.
                # However, we must ensure these paths exist and are valid.
                from src.app.modules.calculation.astrology.brain import calculator as astro  # noqa
                from src.app.modules.calculation.human_design.brain import calculator as hd  # noqa
                from src.app.modules.calculation.numerology.brain import calculator as num  # noqa
                # Add new module imports here as they're created
            except ImportError as e:
                logger.warning(f"Could not import calculator modules: {e}")

            cls._initialized = True


# Convenience function
def get_calculation_modules(has_birth_time: bool = True) -> Dict[str, ModuleMetadata]:
    """Get all enabled calculation modules."""
    return CalculationModuleRegistry.get_modules_for_birth_data(has_birth_time)
