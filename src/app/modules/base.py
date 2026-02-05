"""
GUTTERS - Base Module Class

All GUTTERS modules inherit from this base class to ensure
consistent interface and behavior across the system.

## Brain/Node Separation Pattern

GUTTERS modules follow a Brain/Node architecture for clean separation:

**NODE (module.py)** - Networking and event handling:
- Inherits from BaseModule
- Handles events (birth_data_updated, etc.)
- Publishes results to event bus
- Loads manifest, subscribes to patterns
- Delegates to brain for calculations

**BRAIN (brain/)** - Pure intelligence:
- Pure functions, no event system knowledge
- Can be tested independently
- Swap out calculator without touching networking
- AI interpretation separate from calculation

## Module Directory Structure

```
modules/calculation/astrology/
├── manifest.json         # Module metadata (required)
├── module.py             # NODE - Event handling, subscriptions
├── brain/                # BRAIN - Pure intelligence
│   ├── __init__.py
│   ├── calculator.py     # Pure calculation (Kerykeion wrapper)
│   └── interpreter.py    # AI interpretation (uses LLM)
├── schemas.py            # Data models
└── tests/
```

## Example Implementation

```python
# modules/calculation/astrology/module.py (NODE)
class AstrologyModule(BaseModule):
    async def handle_event(self, packet: Packet) -> None:
        # 1. Extract data from event
        birth_data = packet.payload

        # 2. Delegate to brain (pure function)
        from .brain.calculator import calculate_natal_chart
        chart = calculate_natal_chart(birth_data)

        # 3. Publish result
        await self.event_bus.publish("module.astrology.calculated", chart)

# modules/calculation/astrology/brain/calculator.py (BRAIN)
def calculate_natal_chart(birth_data: dict) -> dict:
    # Pure function - no events, no BaseModule
    from kerykeion import AstrologicalSubject
    subject = AstrologicalSubject(...)
    return subject.natal_aspects()
```

This makes brains reusable, testable, and swappable.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..core.events.bus import get_event_bus
from ..protocol.packet import Packet


class BaseModule(ABC):
    """
    Abstract base class for all GUTTERS modules (the NODE).

    Modules are organized in three layers:
    - Layer 1 (Calculation): Birth data calculations (astrology, numerology, etc.)
    - Layer 2 (Tracking): Real-time cosmic tracking (solar, lunar, planetary)
    - Layer 3 (Intelligence): AI synthesis, learning, features

    Each module must implement:
    - contribute_to_synthesis(): Provide current data for master synthesis

    Lifecycle:
    - __init__(): Load manifest.json
    - initialize(): Load config from DB, subscribe to events
    - handle_event(): React to system events
    - cleanup(): Release resources on shutdown

    Attributes:
        name: Module name (from manifest)
        layer: Module layer (from manifest)
        version: Module version (from manifest)
        manifest: Full manifest dict
        config: Module configuration (loaded from database)
        event_bus: Reference to global event bus
        initialized: Whether initialize() has been called
    """

    # Module metadata (loaded from manifest.json)
    name: str = ""
    layer: str = ""  # "calculation" | "tracking" | "intelligence"
    version: str = "0.1.0"
    description: str = ""

    def __init__(self, manifest_path: Path | None = None):
        """
        Initialize module and load manifest.

        Args:
            manifest_path: Path to manifest.json (optional, auto-detected if subclass
                          is in a standard module directory)
        """
        self.initialized = False
        self.manifest: dict[str, Any] = {}
        self.config: dict[str, Any] = {}
        self.event_bus = get_event_bus()

        # Load manifest
        if manifest_path is None:
            # Try to find manifest.json in the same directory as the subclass
            manifest_path = self._find_manifest_path()

        if manifest_path and manifest_path.exists():
            self._load_manifest(manifest_path)

        # Auto-register with the ModuleRegistry
        if self.name:
            from .registry import ModuleRegistry

            ModuleRegistry.register(self)

    def _find_manifest_path(self) -> Path | None:
        """
        Attempt to find manifest.json in the module's directory.

        Returns:
            Path to manifest.json or None if not found
        """
        # Get the path of the subclass file
        import inspect

        subclass_file = inspect.getfile(self.__class__)
        module_dir = Path(subclass_file).parent
        manifest_path = module_dir / "manifest.json"

        return manifest_path if manifest_path.exists() else None

    def _load_manifest(self, manifest_path: Path) -> None:
        """
        Load and validate manifest.json.

        Args:
            manifest_path: Path to manifest.json

        Raises:
            ValueError: If manifest is missing required fields
        """
        with open(manifest_path) as f:
            self.manifest = json.load(f)

        # Validate required fields
        required_fields = ["name", "version"]
        for field in required_fields:
            if field not in self.manifest:
                raise ValueError(f"Manifest missing required field: {field}")

        # Populate module metadata from manifest
        self.name = self.manifest["name"]
        self.version = self.manifest.get("version", "0.1.0")
        self.layer = self.manifest.get("layer", "")
        self.description = self.manifest.get("description", "")

    async def initialize(self) -> None:
        """
        Called on application startup.

        Default implementation:
        1. Loads configuration from database (system_configurations table)
        2. Subscribes to events listed in manifest["subscriptions"]

        Override to add module-specific initialization, but call super().initialize()
        to retain default behavior.

        Example:
            async def initialize(self) -> None:
                await super().initialize()
                # Module-specific setup
                self.ephemeris = await load_ephemeris()
        """
        # Subscribe to events from manifest
        subscriptions = self.manifest.get("subscriptions", [])
        for pattern in subscriptions:
            await self.event_bus.subscribe(pattern, self.handle_event)

        self.initialized = True

    @abstractmethod
    async def contribute_to_synthesis(self, user_id: str) -> dict[str, Any]:
        """
        Return data for master synthesis engine.

        Args:
            user_id: User UUID to generate synthesis for

        Returns:
            Dict containing module's contribution:
            {
                "module": self.name,
                "layer": self.layer,
                "data": {...},           # Module-specific data
                "insights": [...],       # Key insights (strings)
                "metadata": {...}        # Optional metadata
            }
        """
        pass

    async def cleanup(self) -> None:
        """
        Called on application shutdown (optional).

        Use this to:
        - Close connections
        - Save state
        - Release resources
        """
        pass

    async def handle_event(self, packet: Packet) -> None:
        """
        Handle system events.

        Override to react to events this module subscribes to.
        Remember the Brain/Node pattern: extract data, delegate to brain,
        publish results.

        Args:
            packet: Event packet with event_type and payload

        Example:
            async def handle_event(self, packet: Packet) -> None:
                if packet.event_type == "user.birth_data_updated":
                    # Delegate to brain
                    from .brain.calculator import calculate_chart
                    chart = calculate_chart(packet.payload)

                    # Publish result
                    await self.event_bus.publish(
                        "module.astrology.calculated",
                        chart,
                        source=self.name
                    )
        """
        pass
