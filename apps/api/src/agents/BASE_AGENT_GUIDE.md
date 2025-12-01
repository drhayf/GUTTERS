# BaseAgent Architecture Guide

**Project Sovereign - Agent Development Standard**

This guide provides everything you need to create new agents or extend existing ones while maintaining type safety and architectural consistency.

---

## 📋 Table of Contents

1. [Core Concepts](#core-concepts)
2. [Type Contract (CRITICAL)](#type-contract-critical)
3. [Creating a New Agent](#creating-a-new-agent)
4. [Best Practices](#best-practices)
5. [Common Patterns](#common-patterns)
6. [Testing & Validation](#testing--validation)
7. [Troubleshooting](#troubleshooting)

---

## Core Concepts

### What is BaseAgent?

`BaseAgent` is the **abstract base class** that defines the interface ALL agents must implement. It ensures:

- **Type safety** via Pydantic models
- **Consistent API** across all agents
- **Interoperability** with routers, orchestrator, and swarm bus
- **Automatic registration** in the agent registry

### Key Files

```
apps/api/src/
├── agents/
│   ├── base.py                    # BaseAgent abstract class (SOURCE OF TRUTH)
│   ├── genesis_profiler.py        # Reference implementation
│   └── registry.py                # Auto-discovery system
├── core/
│   └── schemas.py                 # Pydantic models (AgentInput, AgentOutput)
└── routers/
    └── agents.py                  # API endpoints that consume agents
```

---

## Type Contract (CRITICAL)

### The Golden Rule

```python
async def execute(
    self,
    agent_input: AgentInput,      # ✅ MUST accept AgentInput
    model: str = None,             # ✅ OPTIONAL model override
    session_id: str = None         # ✅ OPTIONAL session tracking
) -> AgentOutput:                  # ✅ MUST return AgentOutput
    """Execute the agent with optional model override and session tracking."""
    pass
```

### Input Schema (AgentInput)

```python
class AgentContext(BaseModel):
    birthData: Optional[BirthData] = None      # For astrology/HD agents
    healthMetrics: Optional[dict[str, Any]] = None
    journalThemes: Optional[list[str]] = None
    userQuery: Optional[str] = None            # User's question/request

class AgentInput(BaseModel):
    framework: str          # e.g., "genesis", "human_design", "finance"
    context: AgentContext   # Flexible context object
```

**Access pattern (Pydantic models use attributes, not .get()):**
```python
# ✅ CORRECT
user_query = agent_input.context.userQuery
birth_data = agent_input.context.birthData

# ❌ WRONG - Will crash!
user_query = agent_input.get("context", {}).get("userQuery")
```

### Output Schema (AgentOutput)

```python
class AgentOutput(BaseModel):
    interpretationSeed: str                      # Main response text (REQUIRED)
    method: str                                  # Agent method used (REQUIRED)
    confidence: Optional[float] = Field(ge=0, le=1)  # Confidence score
    calculation: Optional[Any] = None            # Raw calculations/data
    correlations: Optional[list[str]] = None     # Related insights
    visualizationData: Optional[Any] = None      # UI rendering data
```

**All agents MUST return AgentOutput:**
```python
# ✅ CORRECT
return AgentOutput(
    interpretationSeed="Your astrological profile suggests...",
    method="human_design_calculator",
    confidence=0.85,
    calculation={"type": "Manifesting Generator", "profile": "6/2"},
    visualizationData={"chart_data": {...}}
)

# ❌ WRONG - Never return raw dicts!
return {
    "interpretationSeed": "...",
    "method": "..."
}
```

---

## Creating a New Agent

### Step 1: Define Your Agent Class

```python
# apps/api/src/agents/my_new_agent.py

from typing import Optional, Dict, Any
from .base import BaseAgent
from ..core.schemas import AgentInput, AgentOutput

class MyNewAgent(BaseAgent):
    """
    Brief description of what this agent does.
    
    Capabilities:
    - Capability 1
    - Capability 2
    """
    
    # Required class attributes
    name = "my_new_agent"
    description = "Analyzes X using Y framework"
    frameworks = ["framework_name"]  # e.g., ["human_design", "astrology"]
    version = "1.0.0"
    capabilities = ["analyze", "calculate", "interpret"]
    requires_hrm = False  # Set True if agent needs deep reasoning
    
    def __init__(self):
        """Initialize any state, LLM clients, or resources."""
        super().__init__()
        # Your initialization code here
        self.llm = None  # Setup LLM if needed
        self.cache = {}  # Any internal state
```

### Step 2: Implement the execute() Method

```python
    async def execute(
        self,
        agent_input: AgentInput,
        model: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AgentOutput:
        """
        Main execution method.
        
        Args:
            agent_input: Validated input with context
            model: Optional model override (e.g., "gemini-2.5-flash")
            session_id: Optional session ID for stateful interactions
            
        Returns:
            AgentOutput with results
        """
        # 1. Extract data from input
        user_query = agent_input.context.userQuery or ""
        birth_data = agent_input.context.birthData
        
        # 2. Validate required data
        if not birth_data:
            return AgentOutput(
                interpretationSeed="Please provide birth data for analysis.",
                method=f"{self.name}_validation_error",
                confidence=0.0
            )
        
        # 3. Perform your agent's logic
        calculation = await self._perform_calculation(birth_data)
        interpretation = await self._generate_interpretation(calculation, user_query)
        
        # 4. Return AgentOutput (ALWAYS!)
        return AgentOutput(
            interpretationSeed=interpretation,
            method=f"{self.name}_analysis",
            confidence=0.85,
            calculation=calculation,
            visualizationData=self._create_visualization_data(calculation)
        )
```

### Step 3: Implement Helper Methods

```python
    async def _perform_calculation(self, birth_data: BirthData) -> Dict[str, Any]:
        """Internal calculation logic - can return dict."""
        # Your calculation logic here
        return {
            "result": "...",
            "data": {...}
        }
    
    async def _generate_interpretation(
        self, 
        calculation: Dict[str, Any],
        user_query: str
    ) -> str:
        """Generate human-readable interpretation."""
        # Your interpretation logic
        return "Your analysis shows..."
    
    def _create_visualization_data(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for frontend visualization."""
        return {
            "chart_type": "...",
            "data_points": [...]
        }
```

### Step 4: Register Your Agent

```python
# apps/api/src/agents/registry.py (auto-discovery)

# Your agent will be auto-discovered if it follows naming conventions:
# - File name: {name}_agent.py or {name}.py
# - Class name: {Name}Agent
# - Located in: apps/api/src/agents/

# Manual registration (if needed):
from .my_new_agent import MyNewAgent

registry.register(MyNewAgent())
```

---

## Best Practices

### ✅ DO

1. **Always return AgentOutput** from `execute()`
2. **Use attribute access** for Pydantic models: `agent_input.context.userQuery`
3. **Handle missing data gracefully** with validation
4. **Use internal methods** that return dicts (flexibility)
5. **Convert to AgentOutput at the boundary** (public API)
6. **Type hint everything** for IDE support and validation
7. **Document capabilities** in class docstring
8. **Set `requires_hrm=True`** if agent needs deep reasoning

### ❌ DON'T

1. **Never return dicts** from `execute()` method
2. **Never use `.get()`** on Pydantic models
3. **Never modify `AgentInput`** (treat as immutable)
4. **Don't block the event loop** (use async/await)
5. **Don't store user data** in class attributes (use sessions)
6. **Don't assume context fields exist** (always check Optional fields)

---

## Common Patterns

### Pattern 1: Dict-to-AgentOutput Converter

When internal methods return dicts, convert at the boundary:

```python
def _dict_to_agent_output(self, result: Dict[str, Any]) -> AgentOutput:
    """Convert internal dict format to AgentOutput."""
    return AgentOutput(
        interpretationSeed=result.get('message', ''),
        method=result.get('method', self.name),
        confidence=result.get('confidence', 0.5),
        calculation=result.get('calculation'),
        correlations=result.get('correlations'),
        visualizationData=result.get('visualization')
    )

async def execute(self, agent_input: AgentInput, ...) -> AgentOutput:
    result = await self._internal_processing()  # Returns dict
    return self._dict_to_agent_output(result)   # Convert to AgentOutput
```

### Pattern 2: Handling Both Dict and Pydantic Inputs

Sometimes you need backward compatibility:

```python
async def execute(
    self,
    agent_input: Union[Dict[str, Any], AgentInput],
    model: Optional[str] = None,
    session_id: Optional[str] = None
) -> AgentOutput:
    # Handle both types
    if isinstance(agent_input, AgentInput):
        # Pydantic model - use attribute access
        user_query = agent_input.context.userQuery or ""
    else:
        # Dict - use .get()
        context = agent_input.get("context", {})
        user_query = context.get("userQuery", "")
    
    # Rest of your logic...
```

### Pattern 3: Using Model Override

```python
async def execute(self, agent_input: AgentInput, model: Optional[str] = None, ...) -> AgentOutput:
    from ..core.llm_factory import LLMFactory
    
    # Use provided model or default
    active_model = model or "gemini-2.5-flash"
    llm = LLMFactory.get_llm(active_model)
    
    # Use LLM for processing
    response = await llm.ainvoke("Your prompt...")
    
    return AgentOutput(...)
```

### Pattern 4: Session State Management

```python
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    async def execute(self, agent_input: AgentInput, model=None, session_id=None) -> AgentOutput:
        session_id = session_id or "default"
        
        # Get or create session state
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "turn_count": 0,
                "history": []
            }
        
        session = self.sessions[session_id]
        session["turn_count"] += 1
        
        # Your logic using session state...
        
        return AgentOutput(...)
```

### Pattern 5: Error Handling

```python
async def execute(self, agent_input: AgentInput, ...) -> AgentOutput:
    try:
        # Your processing logic
        result = await self._process(agent_input)
        
        return AgentOutput(
            interpretationSeed=result,
            method=self.name,
            confidence=0.85
        )
        
    except ValueError as e:
        # Validation errors - return low confidence
        return AgentOutput(
            interpretationSeed=f"Invalid input: {str(e)}",
            method=f"{self.name}_error",
            confidence=0.0
        )
        
    except Exception as e:
        # Unexpected errors - log and return error state
        print(f"Error in {self.name}: {e}")
        return AgentOutput(
            interpretationSeed="An error occurred during processing.",
            method=f"{self.name}_error",
            confidence=0.0
        )
```

---

## Testing & Validation

### Manual Testing

```python
# test_my_agent.py

from src.agents.my_new_agent import MyNewAgent
from src.core.schemas import AgentInput, AgentContext, BirthData, Location

async def test_agent():
    agent = MyNewAgent()
    
    # Create test input
    agent_input = AgentInput(
        framework="my_framework",
        context=AgentContext(
            userQuery="Tell me about myself",
            birthData=BirthData(
                date="1990-01-01",
                time="12:00",
                location=Location(latitude=40.7128, longitude=-74.0060)
            )
        )
    )
    
    # Execute
    output = await agent.execute(agent_input)
    
    # Validate
    assert isinstance(output, AgentOutput)
    assert output.interpretationSeed != ""
    assert 0 <= output.confidence <= 1
    print(f"✅ Test passed: {output.interpretationSeed[:50]}...")

# Run test
import asyncio
asyncio.run(test_agent())
```

### Automated Validation

Use the type contract validation script:

```bash
cd apps/api
python scripts/validate_type_contracts.py
```

This checks:
- ✅ `execute()` return type is `AgentOutput`
- ✅ No dict returns from `execute()`
- ⚠️  Suspicious `.get()` calls on Pydantic models

---

## Troubleshooting

### Error: `'AgentInput' object has no attribute 'get'`

**Problem:** Calling `.get()` on a Pydantic model

```python
# ❌ WRONG
user_query = agent_input.get("context", {}).get("userQuery")

# ✅ CORRECT
user_query = agent_input.context.userQuery
```

### Error: `'dict' object has no attribute 'interpretationSeed'`

**Problem:** Returning dict instead of AgentOutput

```python
# ❌ WRONG
return {"interpretationSeed": "...", "method": "..."}

# ✅ CORRECT
return AgentOutput(interpretationSeed="...", method="...")
```

### Error: `Field required` or validation errors

**Problem:** Missing required fields in AgentOutput

```python
# ❌ WRONG - missing required fields
return AgentOutput(confidence=0.5)

# ✅ CORRECT - all required fields present
return AgentOutput(
    interpretationSeed="Response text here",  # REQUIRED
    method="agent_name",                      # REQUIRED
    confidence=0.5
)
```

### Warning: Agent not auto-discovered

**Problem:** File or class naming doesn't follow conventions

**Solution:**
1. File name should end with `_agent.py` or be descriptive
2. Class name should end with `Agent`
3. Or manually register in `registry.py`:

```python
from .my_new_agent import MyNewAgent
registry.register(MyNewAgent())
```

---

## Reference Implementation

See **`genesis_profiler.py`** for a complete, production-ready example that demonstrates:

- ✅ Union input handling (Dict | AgentInput)
- ✅ Dict-to-AgentOutput converter
- ✅ Session management
- ✅ Model override usage
- ✅ Error handling
- ✅ Complex multi-phase logic

---

## Quick Checklist

Before deploying a new agent:

- [ ] Class extends `BaseAgent`
- [ ] `execute()` accepts `AgentInput` (or `Union[Dict, AgentInput]`)
- [ ] `execute()` returns `AgentOutput` (never dict!)
- [ ] Required fields set: `name`, `description`, `frameworks`
- [ ] Type hints on all methods
- [ ] Docstrings explain purpose and behavior
- [ ] Tested with validation script
- [ ] Handles missing context fields gracefully
- [ ] Uses attribute access for Pydantic models
- [ ] Registered in agent registry

---

## Questions?

**Where to look:**
- `base.py` - Interface definition
- `schemas.py` - Input/Output models
- `genesis_profiler.py` - Reference implementation
- `validate_type_contracts.py` - Type checking tool

**Key principle:** 
> Internal flexibility (dicts) + Boundary safety (Pydantic) = Clean architecture

---

*Last updated: November 30, 2025*
