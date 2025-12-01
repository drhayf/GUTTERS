"""
Sovereign Tools - Action Capabilities for the Omniscient Agent

This module defines the tool system that enables the Sovereign Agent to
TAKE ACTIONS - not just respond, but actually DO things in the system.

Tool Categories:
━━━━━━━━━━━━━━━━━
1. DATA TOOLS - Query and modify data across modules
2. MODULE TOOLS - Interact with specific domain modules
3. SYSTEM TOOLS - System-level operations
4. UI TOOLS - Generate UI components and overlays
5. SCHEDULING TOOLS - Time-based operations

Architecture:
━━━━━━━━━━━━━━━━━
Each tool follows the pattern:
    - name: Unique identifier
    - description: What it does (for LLM to understand)
    - parameters: JSON Schema of inputs
    - execute(): Async function to perform the action

The toolkit registers tools and provides them to the LLM for function calling.

@module SovereignTools
"""

from typing import (
    Optional, Any, Dict, List, Callable, Awaitable, 
    Type, TypeVar, Generic, Union
)
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from uuid import uuid4
import logging
import json

from pydantic import BaseModel, Field

from ...shared.protocol import (
    SovereignPacket,
    InsightType,
    TargetLayer,
    AgentCapability,
    create_packet,
)

logger = logging.getLogger(__name__)


# =============================================================================
# TOOL RESULT TYPES
# =============================================================================

class ToolResultType(str, Enum):
    """The type of result a tool returns."""
    SUCCESS = "success"
    PARTIAL = "partial"       # Partially completed
    NEEDS_CONFIRMATION = "needs_confirmation"  # Requires user approval
    NEEDS_INPUT = "needs_input"  # Missing required info
    ERROR = "error"
    NOT_AVAILABLE = "not_available"  # Module not enabled


@dataclass
class ToolResult:
    """
    The result of executing a tool.
    
    Contains:
    - The result type (success, error, needs_confirmation, etc.)
    - The actual data/response
    - Optional UI components to render
    - Optional follow-up suggestions
    """
    result_type: ToolResultType
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    
    # UI Generation
    ui_components: List[Dict[str, Any]] = field(default_factory=list)
    
    # For needs_confirmation type
    confirmation_prompt: Optional[str] = None
    confirmation_options: Optional[List[str]] = None
    
    # For needs_input type
    required_inputs: Optional[List[Dict[str, Any]]] = None
    
    # Follow-up suggestions
    suggestions: List[str] = field(default_factory=list)
    
    # Metadata
    executed_at: datetime = field(default_factory=datetime.utcnow)
    execution_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_type": self.result_type.value,
            "message": self.message,
            "data": self.data,
            "ui_components": self.ui_components,
            "confirmation_prompt": self.confirmation_prompt,
            "confirmation_options": self.confirmation_options,
            "required_inputs": self.required_inputs,
            "suggestions": self.suggestions,
            "executed_at": self.executed_at.isoformat(),
            "execution_time_ms": self.execution_time_ms,
        }


# =============================================================================
# BASE TOOL CLASS
# =============================================================================

class ToolParameter(BaseModel):
    """A parameter for a tool."""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[str]] = None
    # For array types, describe the item schema
    items: Optional[Dict[str, Any]] = None
    # For object types, describe properties
    properties: Optional[Dict[str, Any]] = None


class BaseSovereignTool(ABC):
    """
    Abstract base class for all Sovereign tools.
    
    Subclass this to create new tools that the Sovereign Agent can use.
    
    Example:
        class AddNutritionTool(BaseSovereignTool):
            name = "add_nutrition_entry"
            description = "Add a food item to the user's nutrition log"
            category = "nutrition"
            required_capability = AgentCapability.FOOD_ANALYSIS
            
            def get_parameters(self) -> List[ToolParameter]:
                return [
                    ToolParameter(name="food_name", type="string", description="Name of the food"),
                    ToolParameter(name="calories", type="number", description="Calorie count"),
                    ToolParameter(name="meal_type", type="string", enum=["breakfast", "lunch", "dinner", "snack"]),
                ]
            
            async def execute(self, params: Dict, context: "SovereignContext") -> ToolResult:
                # Implementation...
    """
    
    # Metadata
    name: str
    description: str
    category: str = "general"
    
    # Capability requirements
    required_capability: Optional[AgentCapability] = None
    
    # Execution settings
    requires_confirmation: bool = False
    timeout_ms: int = 30000
    
    @abstractmethod
    def get_parameters(self) -> List[ToolParameter]:
        """Return the parameters this tool accepts."""
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any], context: "SovereignContext") -> ToolResult:
        """Execute the tool with the given parameters."""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the JSON Schema for this tool, suitable for LLM function calling.
        
        Returns format compatible with OpenAI/Gemini function calling.
        """
        parameters = self.get_parameters()
        
        properties = {}
        required = []
        
        for param in parameters:
            prop: Dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            # For array types, include items schema (required by Gemini)
            if param.type == "array" and param.items:
                prop["items"] = param.items
            # For object types, include properties schema
            if param.type == "object" and param.properties:
                prop["properties"] = param.properties
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
    
    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """Validate parameters, return list of errors (empty if valid)."""
        errors = []
        parameters = self.get_parameters()
        
        for param in parameters:
            if param.required and param.name not in params:
                errors.append(f"Missing required parameter: {param.name}")
        
        return errors


# =============================================================================
# BUILT-IN TOOLS
# =============================================================================

class QueryDigitalTwinTool(BaseSovereignTool):
    """Query information from the user's Digital Twin profile."""
    
    name = "query_digital_twin"
    description = "Retrieve specific information from the user's Digital Twin profile. Use this to get details about their Human Design type, archetypes, preferences, or any stored profile data."
    category = "data"
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query_type",
                type="string",
                description="What to query: 'human_design', 'archetypes', 'traits', 'preferences', 'full_profile', or 'specific_field'",
                enum=["human_design", "archetypes", "traits", "preferences", "full_profile", "specific_field"],
            ),
            ToolParameter(
                name="field_path",
                type="string",
                description="Dot-notation path to specific field (e.g., 'human_design.type', 'traits.introversion')",
                required=False,
            ),
        ]
    
    async def execute(self, params: Dict[str, Any], context: "SovereignContext") -> ToolResult:
        from ..genesis.state import GenesisState
        
        query_type = params.get("query_type", "full_profile")
        field_path = params.get("field_path")
        
        # Get the digital twin from context
        digital_twin = context.digital_twin or {}
        
        if not digital_twin:
            return ToolResult(
                result_type=ToolResultType.PARTIAL,
                message="No Digital Twin profile found. The user may not have completed profiling yet.",
                data={"has_profile": False},
                suggestions=["Would you like to start the Genesis profiling process?"],
            )
        
        # Query based on type
        if query_type == "full_profile":
            return ToolResult(
                result_type=ToolResultType.SUCCESS,
                message="Retrieved full Digital Twin profile",
                data={"digital_twin": digital_twin},
            )
        
        elif query_type == "human_design":
            hd_data = digital_twin.get("human_design", {})
            return ToolResult(
                result_type=ToolResultType.SUCCESS,
                message=f"Human Design: {hd_data.get('type', 'Unknown')} with {hd_data.get('authority', 'Unknown')} authority",
                data={"human_design": hd_data},
            )
        
        elif query_type == "archetypes":
            archetypes = digital_twin.get("archetypes", {})
            return ToolResult(
                result_type=ToolResultType.SUCCESS,
                message=f"Primary archetype: {archetypes.get('primary', 'Unknown')}",
                data={"archetypes": archetypes},
            )
        
        elif query_type == "traits":
            traits = digital_twin.get("traits", {})
            return ToolResult(
                result_type=ToolResultType.SUCCESS,
                message=f"Found {len(traits)} recorded traits",
                data={"traits": traits},
            )
        
        elif query_type == "specific_field" and field_path:
            # Navigate the nested dict
            value = digital_twin
            for key in field_path.split("."):
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break
            
            return ToolResult(
                result_type=ToolResultType.SUCCESS if value else ToolResultType.PARTIAL,
                message=f"Value at '{field_path}': {value}" if value else f"Field '{field_path}' not found",
                data={"field": field_path, "value": value},
            )
        
        return ToolResult(
            result_type=ToolResultType.ERROR,
            message=f"Unknown query type: {query_type}",
        )


class SynthesizeCrossModuleTool(BaseSovereignTool):
    """Synthesize insights across multiple modules and data sources."""
    
    name = "synthesize_cross_module"
    description = "Analyze and synthesize data across multiple modules to find patterns, correlations, and insights. Use this when the user asks about relationships between different aspects of their life (e.g., how sleep affects productivity)."
    category = "synthesis"
    required_capability = AgentCapability.SYNTHESIS
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="modules",
                type="array",
                description="List of modules to synthesize: 'nutrition', 'health', 'finance', 'journal', 'human_design'",
            ),
            ToolParameter(
                name="focus_question",
                type="string",
                description="The specific question or pattern to investigate",
            ),
            ToolParameter(
                name="time_range",
                type="string",
                description="Time range to analyze: 'today', 'week', 'month', 'all_time'",
                required=False,
            ),
        ]
    
    async def execute(self, params: Dict[str, Any], context: "SovereignContext") -> ToolResult:
        modules = params.get("modules", [])
        focus_question = params.get("focus_question", "")
        time_range = params.get("time_range", "week")
        
        # Check which modules are available
        available_modules = []
        unavailable_modules = []
        
        capability_map = {
            "nutrition": AgentCapability.FOOD_ANALYSIS,
            "health": AgentCapability.HEALTH_METRICS,
            "finance": AgentCapability.FINANCE,
            "journal": AgentCapability.JOURNALING,
            "human_design": AgentCapability.HUMAN_DESIGN,
        }
        
        for module in modules:
            cap = capability_map.get(module)
            if cap and cap in context.enabled_capabilities:
                available_modules.append(module)
            else:
                unavailable_modules.append(module)
        
        if not available_modules:
            return ToolResult(
                result_type=ToolResultType.NOT_AVAILABLE,
                message="None of the requested modules are enabled",
                data={"unavailable": unavailable_modules},
                suggestions=["Enable the required modules in Settings > Modules"],
            )
        
        # Collect data from each module
        module_data = {}
        
        for module in available_modules:
            # In a real implementation, this would query actual module data
            # For now, we'll use placeholder data from context
            module_data[module] = context.module_data.get(module, {})
        
        # Synthesize (this would use the LLM in full implementation)
        synthesis_result = {
            "modules_analyzed": available_modules,
            "time_range": time_range,
            "focus": focus_question,
            "insights": [],
            "patterns": [],
            "recommendations": [],
        }
        
        return ToolResult(
            result_type=ToolResultType.SUCCESS,
            message=f"Synthesized data from {len(available_modules)} modules",
            data=synthesis_result,
            ui_components=[
                {
                    "type": "synthesis_card",
                    "props": {
                        "title": "Cross-Module Synthesis",
                        "modules": available_modules,
                        "insights": synthesis_result.get("insights", []),
                    },
                },
            ],
        )


class GenerateUITool(BaseSovereignTool):
    """Generate dynamic UI components for rich interactions."""
    
    name = "generate_ui_component"
    description = """Generate a dynamic UI component to display to the user.

COMPONENT SELECTION GUIDE:
• text/insight_card: For explaining concepts, sharing wisdom, displaying information
• choice: For yes/no questions, A/B decisions, selecting from 2-4 options
• slider: For rating scales (1-10), intensity levels, degree measurements
• cards: For multiple selections, category grids, feature selection
• progress: For showing journey progress, completion status

The component will be rendered by the frontend's GenerativeRenderer.
Choose the component type that best matches the interaction goal."""
    category = "ui"
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="component_type",
                type="string",
                description="""Type of component to generate (ONLY use these supported types):
- text: General formatted text with title and content. Use variant to style (question, oracle, insight, completion)
- insight_card: Styled wisdom/insight card (renders as text with insight styling)
- input: Text input field for user to type a response
- progress: Progress indicator showing current step in a flow (use phase, current, total)
- choice: Present 2-4 options for user to select (use options array with label and value)
- binary_choice: Simple Yes/No or two-option choice
- slider: Numeric range selection (use min, max, labels)
- cards: Grid of selectable cards (use cards array with title, value, description, icon)
- digital_twin_card: Display user's Digital Twin profile summary
- activation_steps: Show personalized next steps for user journey""",
                enum=[
                    "text",            # General formatted text display with variant styling
                    "insight_card",    # Styled insight/wisdom card
                    "input",           # Text input field for user responses
                    "progress",        # Progress indicator for flows
                    "choice",          # Present 2-4 options with labels and values
                    "binary_choice",   # Yes/No or two-option choice
                    "slider",          # Numeric range selection
                    "cards",           # Card selection grid for rich options
                    "digital_twin_card",   # Digital Twin profile display
                    "activation_steps",    # Personalized next steps
                ],
            ),
            ToolParameter(
                name="title",
                type="string",
                description="Title displayed at the top of the component",
                required=False,
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Main content/text for text and insight_card components",
                required=False,
            ),
            ToolParameter(
                name="variant",
                type="string",
                description="Visual styling variant for text components",
                enum=["default", "question", "oracle", "insight", "completion"],
                required=False,
            ),
            ToolParameter(
                name="options",
                type="array",
                description="Array of choice options for 'choice' component. Each option needs label (display text) and value (returned when selected).",
                required=False,
                items={
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "description": "Display label for the option"},
                        "value": {"type": "string", "description": "Value returned when selected"},
                    },
                    "required": ["label", "value"],
                },
            ),
            ToolParameter(
                name="cards",
                type="array",
                description="Array of card objects for 'cards' component. Each card needs title and value.",
                required=False,
                items={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Card title"},
                        "value": {"type": "string", "description": "Value returned when selected"},
                        "description": {"type": "string", "description": "Optional card description"},
                        "icon": {"type": "string", "description": "Optional emoji icon"},
                    },
                    "required": ["title", "value"],
                },
            ),
            ToolParameter(
                name="min",
                type="number",
                description="Minimum value for slider component (default: 1)",
                required=False,
            ),
            ToolParameter(
                name="max",
                type="number",
                description="Maximum value for slider component (default: 10)",
                required=False,
            ),
            ToolParameter(
                name="labels",
                type="object",
                description="Labels for slider endpoints, e.g., {\"1\": \"Low\", \"10\": \"High\"}",
                required=False,
                properties={
                    "min_label": {"type": "string"},
                    "max_label": {"type": "string"},
                },
            ),
            ToolParameter(
                name="phase",
                type="string",
                description="Current phase name for progress component",
                required=False,
            ),
            ToolParameter(
                name="current",
                type="number",
                description="Current progress value for progress component",
                required=False,
            ),
            ToolParameter(
                name="total",
                type="number",
                description="Total value for progress component",
                required=False,
            ),
        ]
    
    async def execute(self, params: Dict[str, Any], context: "SovereignContext") -> ToolResult:
        component_type = params.get("component_type", "text")
        
        # Build props based on component type
        props: Dict[str, Any] = {}
        
        # Common props
        if title := params.get("title"):
            props["title"] = title
        if content := params.get("content"):
            props["content"] = content
        if variant := params.get("variant"):
            props["variant"] = variant
            
        # Type-specific props
        if component_type in ("choice", "binary_choice") and (options := params.get("options")):
            props["options"] = options
        elif component_type == "slider":
            props["min"] = params.get("min", 1)
            props["max"] = params.get("max", 10)
            if labels := params.get("labels"):
                props["labels"] = labels
        elif component_type == "progress":
            props["phase"] = params.get("phase", "default")
            props["current"] = params.get("current", 0)
            props["total"] = params.get("total", 100)
        elif component_type == "cards" and (cards := params.get("cards")):
            props["cards"] = cards
        elif component_type == "input":
            props["placeholder"] = params.get("placeholder", "Type your response...")
        elif component_type == "visualization":
            props["data"] = params.get("data", {})
            props["chart_type"] = params.get("chart_type", "bar")
        elif component_type == "digital_twin_card":
            # Digital twin data comes from context
            props["digital_twin"] = params.get("digital_twin", {})
        elif component_type == "activation_steps":
            props["steps"] = params.get("steps", [])
        
        component = {
            "type": component_type,
            "props": props,
        }
        
        # Also add content at root level for frontend compatibility
        if content:
            component["content"] = content
        if variant:
            component["variant"] = variant
        
        return ToolResult(
            result_type=ToolResultType.SUCCESS,
            message=f"Generated {component_type} component" + (f": {title}" if title else ""),
            ui_components=[component],
        )


class AddNutritionEntryTool(BaseSovereignTool):
    """Add a food entry to the nutrition log."""
    
    name = "add_nutrition_entry"
    description = "Add a food item or meal to the user's nutrition log. Use this when the user mentions eating something or wants to track their food."
    category = "nutrition"
    required_capability = AgentCapability.FOOD_ANALYSIS
    requires_confirmation = True
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="food_name",
                type="string",
                description="Name of the food or meal",
            ),
            ToolParameter(
                name="meal_type",
                type="string",
                description="Type of meal",
                enum=["breakfast", "lunch", "dinner", "snack"],
            ),
            ToolParameter(
                name="calories",
                type="number",
                description="Estimated calories (optional)",
                required=False,
            ),
            ToolParameter(
                name="notes",
                type="string",
                description="Additional notes about the meal",
                required=False,
            ),
        ]
    
    async def execute(self, params: Dict[str, Any], context: "SovereignContext") -> ToolResult:
        food_name = params.get("food_name")
        meal_type = params.get("meal_type", "snack")
        calories = params.get("calories")
        notes = params.get("notes", "")
        
        # Check if nutrition module is enabled
        if AgentCapability.FOOD_ANALYSIS not in context.enabled_capabilities:
            return ToolResult(
                result_type=ToolResultType.NOT_AVAILABLE,
                message="The Nutrition module is not enabled",
                suggestions=["Enable the Nutrition module in Settings > Modules"],
            )
        
        # Create the entry
        entry = {
            "id": str(uuid4()),
            "food_name": food_name,
            "meal_type": meal_type,
            "calories": calories,
            "notes": notes,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # In full implementation, this would persist to the nutrition module
        return ToolResult(
            result_type=ToolResultType.NEEDS_CONFIRMATION,
            message=f"Ready to log: {food_name} ({meal_type})",
            data={"entry": entry},
            confirmation_prompt=f"Add '{food_name}' to your {meal_type} log?",
            confirmation_options=["Yes, add it", "Edit details", "Cancel"],
            ui_components=[
                {
                    "type": "nutrition_entry_preview",
                    "props": {
                        "food_name": food_name,
                        "meal_type": meal_type,
                        "calories": calories,
                        "notes": notes,
                    },
                },
            ],
        )


class ListEnabledModulesTool(BaseSovereignTool):
    """List all enabled modules and their status."""
    
    name = "list_enabled_modules"
    description = "Get a list of all modules that are currently enabled for the user, along with their status and capabilities."
    category = "system"
    
    def get_parameters(self) -> List[ToolParameter]:
        return []  # No parameters needed
    
    async def execute(self, params: Dict[str, Any], context: "SovereignContext") -> ToolResult:
        enabled = list(context.enabled_capabilities)
        
        module_info = []
        for cap in enabled:
            module_info.append({
                "capability": cap.value,
                "name": cap.value.replace("_", " ").title(),
                "enabled": True,
            })
        
        return ToolResult(
            result_type=ToolResultType.SUCCESS,
            message=f"You have {len(enabled)} modules enabled",
            data={
                "enabled_modules": module_info,
                "total_count": len(enabled),
            },
            ui_components=[
                {
                    "type": "module_list",
                    "props": {
                        "modules": module_info,
                    },
                },
            ],
        )


class GetSystemStatusTool(BaseSovereignTool):
    """Get the current system status and health."""
    
    name = "get_system_status"
    description = "Get the current status of the Sovereign system including agent health, connected modules, and any active processes."
    category = "system"
    
    def get_parameters(self) -> List[ToolParameter]:
        return []
    
    async def execute(self, params: Dict[str, Any], context: "SovereignContext") -> ToolResult:
        # In full implementation, this would check actual system status
        status = {
            "system_health": "operational",
            "active_agents": [
                "sovereign",
                "genesis",
                "orchestrator",
            ],
            "profile_status": "complete" if context.digital_twin else "incomplete",
            "enabled_modules": len(context.enabled_capabilities),
            "session_id": context.session_id,
            "uptime": "active",
        }
        
        return ToolResult(
            result_type=ToolResultType.SUCCESS,
            message="System operational",
            data=status,
        )


# =============================================================================
# TOOLKIT REGISTRY
# =============================================================================

class SovereignToolkit:
    """
    Registry and manager for all Sovereign tools.
    
    The toolkit:
    - Registers all available tools
    - Provides them to the LLM for function calling
    - Executes tool calls and returns results
    - Filters tools based on enabled capabilities
    
    Usage:
        toolkit = SovereignToolkit()
        toolkit.register_defaults()
        
        # Get tools for LLM
        available_tools = toolkit.get_available_tools(context)
        
        # Execute a tool
        result = await toolkit.execute("add_nutrition_entry", params, context)
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseSovereignTool] = {}
    
    def register(self, tool: BaseSovereignTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info(f"[SovereignToolkit] Registered tool: {tool.name}")
    
    def register_defaults(self) -> None:
        """Register all built-in tools."""
        self.register(QueryDigitalTwinTool())
        self.register(SynthesizeCrossModuleTool())
        self.register(GenerateUITool())
        self.register(AddNutritionEntryTool())
        self.register(ListEnabledModulesTool())
        self.register(GetSystemStatusTool())
    
    def get(self, name: str) -> Optional[BaseSovereignTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all(self) -> List[BaseSovereignTool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_available_tools(self, context: "SovereignContext") -> List[BaseSovereignTool]:
        """
        Get tools available for the given context.
        
        Filters out tools that require capabilities the user hasn't enabled.
        """
        available = []
        
        for tool in self._tools.values():
            if tool.required_capability is None:
                # No capability requirement
                available.append(tool)
            elif tool.required_capability in context.enabled_capabilities:
                # User has the required capability
                available.append(tool)
        
        return available
    
    def get_tool_schemas(self, context: "SovereignContext") -> List[Dict[str, Any]]:
        """Get JSON schemas for all available tools (for LLM function calling)."""
        available = self.get_available_tools(context)
        return [tool.get_schema() for tool in available]
    
    async def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: "SovereignContext",
    ) -> ToolResult:
        """
        Execute a tool by name.
        
        Args:
            tool_name: The name of the tool to execute
            params: Parameters for the tool
            context: The current sovereign context
        
        Returns:
            ToolResult with the execution outcome
        """
        tool = self.get(tool_name)
        
        if not tool:
            return ToolResult(
                result_type=ToolResultType.ERROR,
                message=f"Unknown tool: {tool_name}",
            )
        
        # Check capability
        if tool.required_capability and tool.required_capability not in context.enabled_capabilities:
            return ToolResult(
                result_type=ToolResultType.NOT_AVAILABLE,
                message=f"The {tool.category} module is not enabled",
                suggestions=[f"Enable the module in Settings > Modules"],
            )
        
        # Validate params
        errors = tool.validate_params(params)
        if errors:
            return ToolResult(
                result_type=ToolResultType.ERROR,
                message="Invalid parameters: " + ", ".join(errors),
            )
        
        # Execute
        start = datetime.utcnow()
        try:
            result = await tool.execute(params, context)
            result.execution_time_ms = (datetime.utcnow() - start).total_seconds() * 1000
            return result
        except Exception as e:
            logger.error(f"[SovereignToolkit] Tool {tool_name} failed: {e}")
            return ToolResult(
                result_type=ToolResultType.ERROR,
                message=f"Tool execution failed: {str(e)}",
            )


# Import SovereignContext at runtime to avoid circular imports
if False:  # TYPE_CHECKING
    from .agent import SovereignContext
