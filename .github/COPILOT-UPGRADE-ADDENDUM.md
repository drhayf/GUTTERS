# COPILOT-UPGRADE Addendum: Missing Capabilities
## Complete System Integration Layer

> This addendum addresses capabilities NOT covered in the main COPILOT-UPGRADE.md, ensuring the system has **complete awareness**, **real-time sync**, **unified querying**, and **live integration testing**.

---

## 🧠 THE AWARENESS LAYER

The key insight: The Sovereign Agent needs a **single interface** to understand the entire system state at any moment. This is the **Awareness Layer**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AWARENESS LAYER                                    │
│            (The Sovereign Agent's "All-Seeing Eye")                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   UNIFIED   │  │  REAL-TIME  │  │  GLOBAL     │  │   LIVE      │        │
│  │   QUERY     │  │  EVENT      │  │  STATE      │  │   TESTING   │        │
│  │   INTERFACE │  │  STREAM     │  │  SNAPSHOT   │  │   SYSTEM    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                    │                                        │
│                         ┌──────────▼──────────┐                             │
│                         │   AWARENESS CORE    │                             │
│                         │  • System Introspection                           │
│                         │  • Cross-Domain Correlation                       │
│                         │  • Health Monitoring                              │
│                         │  • Event Aggregation                              │
│                         └──────────┬──────────┘                             │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐            │
│         ▼                          ▼                          ▼            │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐        │
│  │  DIGITAL    │          │   AGENT     │          │    CORE     │        │
│  │   TWIN      │          │   SWARM     │          │   SYSTEMS   │        │
│  │  (Domains)  │          │  (Agents)   │          │  (HRM, LLM) │        │
│  └─────────────┘          └─────────────┘          └─────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 ADDITIONAL FRACTAL STRUCTURES

### 1. Awareness Layer (`apps/api/src/awareness/`)

```
awareness/
├── __init__.py
├── definition.py              # AwarenessCore class
├── schema.py                  # SystemState, QueryResult, etc.
│
├── query/                     # 🔍 UNIFIED QUERY INTERFACE
│   ├── __init__.py
│   ├── definition.py          # UnifiedQueryEngine
│   ├── schema.py              # Query, QueryResult, Filter
│   ├── parser/                # Query DSL parser
│   │   ├── __init__.py
│   │   ├── lexer/
│   │   └── ast/
│   ├── executors/             # Domain-specific query execution
│   │   ├── __init__.py
│   │   ├── digital_twin/
│   │   ├── agents/
│   │   ├── events/
│   │   └── config/
│   └── aggregators/           # Cross-domain result merging
│       ├── __init__.py
│       ├── union/
│       ├── intersection/
│       └── correlation/
│
├── events/                    # 📡 REAL-TIME EVENT STREAM
│   ├── __init__.py
│   ├── definition.py          # GlobalEventBus
│   ├── schema.py              # Event, Subscription, Filter
│   ├── bus/
│   │   ├── __init__.py
│   │   ├── publisher/
│   │   ├── subscriber/
│   │   └── router/
│   ├── streams/               # Event stream types
│   │   ├── __init__.py
│   │   ├── trait_changes/
│   │   ├── agent_messages/
│   │   ├── user_actions/
│   │   ├── system_health/
│   │   └── notifications/
│   ├── filters/               # Event filtering
│   │   ├── __init__.py
│   │   ├── by_domain/
│   │   ├── by_type/
│   │   ├── by_priority/
│   │   └── by_source/
│   └── persistence/           # Event history
│       ├── __init__.py
│       ├── store/
│       └── replay/
│
├── state/                     # 🌍 GLOBAL STATE SNAPSHOT
│   ├── __init__.py
│   ├── definition.py          # GlobalStateManager
│   ├── schema.py              # SystemSnapshot, ComponentState
│   ├── collectors/            # State collection from each system
│   │   ├── __init__.py
│   │   ├── digital_twin/
│   │   ├── agents/
│   │   ├── swarm_bus/
│   │   ├── orchestrator/
│   │   ├── sessions/
│   │   └── config/
│   ├── snapshot/              # Point-in-time snapshots
│   │   ├── __init__.py
│   │   ├── creator/
│   │   ├── differ/            # Diff between snapshots
│   │   └── restorer/
│   └── watchers/              # State change detection
│       ├── __init__.py
│       └── triggers/
│
├── notifications/             # 🔔 NOTIFICATION SYSTEM
│   ├── __init__.py
│   ├── definition.py          # NotificationManager
│   ├── schema.py              # Notification, Channel, Priority
│   ├── channels/              # Delivery channels
│   │   ├── __init__.py
│   │   ├── in_app/            # Push to frontend overlay
│   │   ├── push/              # Mobile push notifications
│   │   ├── email/             # Email notifications
│   │   └── webhook/           # External webhooks
│   ├── templates/             # Notification templates
│   │   ├── __init__.py
│   │   ├── insight/
│   │   ├── alert/
│   │   ├── reminder/
│   │   └── achievement/
│   ├── rules/                 # When to notify
│   │   ├── __init__.py
│   │   ├── trait_milestone/
│   │   ├── pattern_detected/
│   │   ├── goal_progress/
│   │   └── scheduled/
│   └── preferences/           # User notification preferences
│       ├── __init__.py
│       └── manager/
│
├── introspection/             # 🔬 SYSTEM INTROSPECTION
│   ├── __init__.py
│   ├── definition.py          # SystemIntrospector
│   ├── registry_scanner/      # Scan all registries
│   │   ├── __init__.py
│   │   ├── domains/
│   │   ├── traits/
│   │   ├── agents/
│   │   └── tools/
│   ├── capability_map/        # What can each component do?
│   │   ├── __init__.py
│   │   └── builder/
│   ├── dependency_graph/      # What depends on what?
│   │   ├── __init__.py
│   │   ├── analyzer/
│   │   └── visualizer/
│   └── health/                # Component health status
│       ├── __init__.py
│       ├── checkers/
│       └── reporters/
│
└── correlation/               # 🔗 CROSS-DOMAIN CORRELATION
    ├── __init__.py
    ├── definition.py          # CorrelationEngine
    ├── patterns/              # Correlation patterns
    │   ├── __init__.py
    │   ├── temporal/          # Events close in time
    │   ├── causal/            # A causes B
    │   ├── coincidental/      # Often occur together
    │   └── inverse/           # When A up, B down
    ├── detectors/             # Pattern detection
    │   ├── __init__.py
    │   └── ml/                # ML-based detection
    └── insights/              # Generated insights
        ├── __init__.py
        └── generator/
```

---

### 2. Live Integration Testing (`apps/api/src/integration/`)

This is the **Living Test System** that works with LIVE code, not mocked configurations.

```
integration/
├── __init__.py
├── definition.py              # IntegrationCore
├── schema.py                  # TestCase, TestResult, SystemProbe
│
├── probes/                    # 🔍 SYSTEM PROBES (Live Introspection)
│   ├── __init__.py
│   ├── base.py                # Probe ABC
│   ├── registry.py            # ProbeRegistry
│   │
│   ├── domains/               # Domain health probes
│   │   ├── __init__.py
│   │   ├── genesis/
│   │   │   ├── schema_probe.py     # Can Genesis produce valid schema?
│   │   │   ├── trait_probe.py      # Are all traits properly defined?
│   │   │   └── phase_probe.py      # Do all phases transition correctly?
│   │   ├── health/
│   │   ├── nutrition/
│   │   ├── journaling/
│   │   └── finance/
│   │
│   ├── agents/                # Agent functionality probes
│   │   ├── __init__.py
│   │   ├── sovereign/
│   │   │   ├── tool_probe.py       # Do all tools execute?
│   │   │   ├── routing_probe.py    # Does routing work?
│   │   │   └── memory_probe.py     # Does memory persist?
│   │   ├── genesis/
│   │   │   ├── profiler_probe.py
│   │   │   ├── hypothesis_probe.py
│   │   │   └── face_probe.py
│   │   └── master/
│   │       ├── hypothesis_engine_probe.py
│   │       └── scout_probe.py
│   │
│   ├── communication/         # Inter-component communication
│   │   ├── __init__.py
│   │   ├── swarm_bus/
│   │   │   ├── send_probe.py
│   │   │   ├── broadcast_probe.py
│   │   │   ├── escalate_probe.py
│   │   │   └── delegate_probe.py
│   │   ├── orchestrator/
│   │   │   ├── routing_probe.py
│   │   │   └── state_probe.py
│   │   └── events/
│   │       ├── publish_probe.py
│   │       └── subscribe_probe.py
│   │
│   ├── contracts/             # Schema/contract verification
│   │   ├── __init__.py
│   │   ├── trait_schema_probe.py
│   │   ├── domain_schema_probe.py
│   │   ├── packet_schema_probe.py
│   │   └── api_contract_probe.py
│   │
│   └── awareness/             # Awareness layer probes
│       ├── __init__.py
│       ├── query_probe.py
│       ├── event_probe.py
│       ├── state_probe.py
│       └── notification_probe.py
│
├── scenarios/                 # 📋 TEST SCENARIOS (End-to-End)
│   ├── __init__.py
│   ├── base.py                # Scenario ABC
│   ├── registry.py            # ScenarioRegistry
│   │
│   ├── user_journeys/         # Complete user flows
│   │   ├── __init__.py
│   │   ├── onboarding/
│   │   │   ├── first_open.py
│   │   │   ├── genesis_completion.py
│   │   │   └── profile_save.py
│   │   ├── daily_use/
│   │   │   ├── journal_entry.py
│   │   │   ├── check_insights.py
│   │   │   └── ask_sovereign.py
│   │   └── edge_cases/
│   │       ├── session_recovery.py
│   │       ├── network_failure.py
│   │       └── concurrent_access.py
│   │
│   ├── agent_conversations/   # Multi-turn agent interactions
│   │   ├── __init__.py
│   │   ├── genesis_full_flow.py
│   │   ├── sovereign_commands.py
│   │   └── cross_agent_routing.py
│   │
│   └── system_stress/         # Stress testing
│       ├── __init__.py
│       ├── high_message_volume.py
│       ├── concurrent_sessions.py
│       └── memory_pressure.py
│
├── assertions/                # ✅ ASSERTION LIBRARY
│   ├── __init__.py
│   ├── base.py                # Assertion ABC
│   │
│   ├── schema/                # Schema assertions
│   │   ├── has_required_fields.py
│   │   ├── valid_enum_value.py
│   │   └── matches_contract.py
│   │
│   ├── behavior/              # Behavior assertions
│   │   ├── responds_within.py
│   │   ├── emits_event.py
│   │   ├── updates_state.py
│   │   └── routes_correctly.py
│   │
│   └── data/                  # Data assertions
│       ├── trait_has_value.py
│       ├── domain_has_traits.py
│       └── registry_contains.py
│
├── runners/                   # 🏃 TEST RUNNERS
│   ├── __init__.py
│   ├── cli/                   # Command-line runner
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   └── formatters/
│   │       ├── console/
│   │       ├── json/
│   │       └── html/
│   ├── api/                   # API endpoint for live testing
│   │   ├── __init__.py
│   │   └── router.py          # /integration/run, /integration/status
│   ├── scheduled/             # Scheduled test runs
│   │   ├── __init__.py
│   │   └── cron/
│   └── watch/                 # File watcher for auto-run
│       ├── __init__.py
│       └── trigger/
│
├── reports/                   # 📊 REPORTING
│   ├── __init__.py
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── summary/
│   │   ├── detailed/
│   │   ├── diff/              # What changed since last run?
│   │   └── coverage/          # What's tested vs. not?
│   └── storage/
│       ├── __init__.py
│       └── history/           # Historical test results
│
└── fixtures/                  # 🔧 TEST FIXTURES
    ├── __init__.py
    ├── sessions/              # Pre-configured sessions
    ├── profiles/              # Sample profiles
    ├── conversations/         # Sample conversations
    └── events/                # Sample events
```

---

### 3. Plugin System (`apps/api/src/plugins/`)

For hot-loading new capabilities at runtime.

```
plugins/
├── __init__.py
├── definition.py              # PluginManager
├── schema.py                  # Plugin, PluginManifest, PluginState
│
├── loader/                    # Plugin loading
│   ├── __init__.py
│   ├── discovery/             # Find plugins
│   │   ├── __init__.py
│   │   ├── filesystem/
│   │   └── registry/
│   ├── validator/             # Validate before loading
│   │   ├── __init__.py
│   │   ├── manifest/
│   │   ├── dependencies/
│   │   └── compatibility/
│   └── activator/             # Activate plugin
│       ├── __init__.py
│       └── hooks/
│
├── types/                     # Plugin types
│   ├── __init__.py
│   ├── domain/                # New domain plugins
│   ├── agent/                 # New agent plugins
│   ├── framework/             # New framework plugins
│   ├── voice/                 # New voice plugins
│   ├── tool/                  # New tool plugins
│   └── component/             # New UI component plugins
│
├── sandbox/                   # Plugin isolation
│   ├── __init__.py
│   ├── executor/
│   └── permissions/
│
└── marketplace/               # Plugin discovery/sharing (future)
    ├── __init__.py
    └── registry/
```

---

### 4. Observability Layer (`apps/api/src/observability/`)

For metrics, traces, and comprehensive monitoring.

```
observability/
├── __init__.py
├── definition.py              # ObservabilityCore
│
├── metrics/                   # 📈 METRICS
│   ├── __init__.py
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── agent_metrics/
│   │   ├── domain_metrics/
│   │   ├── api_metrics/
│   │   └── system_metrics/
│   ├── aggregators/
│   └── exporters/
│       ├── prometheus/
│       └── json/
│
├── traces/                    # 🔍 DISTRIBUTED TRACING
│   ├── __init__.py
│   ├── tracer/
│   ├── spans/
│   │   ├── api_request/
│   │   ├── agent_call/
│   │   ├── swarm_message/
│   │   └── llm_call/
│   └── exporters/
│       ├── jaeger/
│       └── console/
│
├── logs/                      # 📝 STRUCTURED LOGGING
│   ├── __init__.py
│   ├── formatters/
│   ├── handlers/
│   └── filters/
│
└── dashboards/                # 📊 DASHBOARDS
    ├── __init__.py
    ├── system_health/
    ├── agent_activity/
    └── user_sessions/
```

---

## 🔗 HOW AWARENESS CONNECTS TO SOVEREIGN AGENT

The Sovereign Agent gains "omniscience" through the Awareness Layer:

```python
# sovereign/agent/integrations/awareness/
class AwarenessIntegration:
    """Gives Sovereign Agent access to the Awareness Layer."""
    
    def __init__(self, awareness: AwarenessCore):
        self.awareness = awareness
    
    # Unified Query - Ask anything
    async def query(self, query_string: str) -> QueryResult:
        """
        Query any data across the entire system.
        
        Examples:
        - "SELECT traits FROM digital_twin WHERE category = 'personality'"
        - "SELECT messages FROM swarm_bus WHERE source = 'genesis'"
        - "SELECT health FROM domains"
        """
        return await self.awareness.query.execute(query_string)
    
    # Real-Time Events - Subscribe to anything
    async def subscribe(self, event_filter: EventFilter) -> EventStream:
        """Subscribe to real-time events matching filter."""
        return await self.awareness.events.subscribe(event_filter)
    
    # Global State - Snapshot of everything
    async def get_state(self) -> SystemSnapshot:
        """Get complete system state at this moment."""
        return await self.awareness.state.snapshot()
    
    # Notifications - Push to user
    async def notify(self, notification: Notification) -> None:
        """Send notification to user."""
        await self.awareness.notifications.send(notification)
    
    # Introspection - What exists?
    async def introspect(self) -> SystemCapabilities:
        """Get map of all system capabilities."""
        return await self.awareness.introspection.scan()
    
    # Correlation - What relates?
    async def correlate(self, entity_a: str, entity_b: str) -> Correlation:
        """Find correlations between two entities."""
        return await self.awareness.correlation.find(entity_a, entity_b)
```

### Sovereign Agent Tools Enhanced

```
sovereign/agent/tools/
├── ...existing tools...
│
├── query_system/              # NEW: Query anything
│   ├── __init__.py
│   ├── definition.py
│   └── executor/
│
├── watch_events/              # NEW: Subscribe to events
│   ├── __init__.py
│   ├── definition.py
│   └── subscriptions/
│
├── send_notification/         # NEW: Push notifications
│   ├── __init__.py
│   ├── definition.py
│   └── templates/
│
├── run_integration_test/      # NEW: Run live tests
│   ├── __init__.py
│   ├── definition.py
│   └── runners/
│
└── inspect_system/            # NEW: System introspection
    ├── __init__.py
    ├── definition.py
    └── reporters/
```

---

## 🧪 LIVE INTEGRATION TESTING IN ACTION

### How It Works

```python
# integration/definition.py
class IntegrationCore:
    """
    The Living Test System.
    
    Unlike traditional tests that mock dependencies,
    this system runs against LIVE code and configurations.
    """
    
    def __init__(self):
        self.probes = ProbeRegistry()
        self.scenarios = ScenarioRegistry()
        self.assertions = AssertionLibrary()
        self.runner = TestRunner()
    
    async def run_probe(self, probe_id: str) -> ProbeResult:
        """
        Run a single probe against live system.
        
        Example:
        >>> result = await core.run_probe("domains.genesis.schema_probe")
        >>> print(result.passed)  # True if Genesis schema is valid
        """
        probe = self.probes.get(probe_id)
        return await probe.execute()
    
    async def run_scenario(self, scenario_id: str) -> ScenarioResult:
        """
        Run end-to-end scenario against live system.
        
        Example:
        >>> result = await core.run_scenario("user_journeys.onboarding.genesis_completion")
        >>> print(result.steps)  # Each step with pass/fail
        """
        scenario = self.scenarios.get(scenario_id)
        return await scenario.execute()
    
    async def run_all(self, filter: Optional[str] = None) -> TestReport:
        """
        Run all probes and scenarios, optionally filtered.
        
        Example:
        >>> report = await core.run_all(filter="domains.*")
        >>> print(report.summary)
        """
        return await self.runner.run_all(filter)
    
    async def watch(self, on_change: Callable) -> None:
        """
        Watch for file changes and auto-run relevant tests.
        
        When genesis/profiler.py changes, automatically runs:
        - probes/agents/genesis/profiler_probe.py
        - scenarios/agent_conversations/genesis_full_flow.py
        """
        await self.runner.watch(on_change)
```

### Example Probe

```python
# integration/probes/domains/genesis/schema_probe.py

from integration.probes.base import Probe, ProbeResult
from digital_twin.domains import GenesisDomain
from digital_twin.traits.categories import TraitCategory

class GenesisSchemaProbe(Probe):
    """
    Verifies Genesis domain schema is correctly defined.
    
    This probe runs against the ACTUAL GenesisDomain class,
    not a mock or test double.
    """
    
    id = "domains.genesis.schema_probe"
    description = "Verify Genesis domain produces valid schema"
    
    async def execute(self) -> ProbeResult:
        results = []
        
        # 1. Can we instantiate?
        try:
            domain = GenesisDomain()
            results.append(("instantiation", True, "GenesisDomain instantiated"))
        except Exception as e:
            results.append(("instantiation", False, str(e)))
            return ProbeResult(passed=False, checks=results)
        
        # 2. Does get_schema() work?
        try:
            schema = domain.get_schema()
            results.append(("get_schema", True, "Schema generated"))
        except Exception as e:
            results.append(("get_schema", False, str(e)))
            return ProbeResult(passed=False, checks=results)
        
        # 3. Are there traits?
        trait_count = len(schema.traits)
        if trait_count > 0:
            results.append(("has_traits", True, f"{trait_count} traits found"))
        else:
            results.append(("has_traits", False, "No traits in schema"))
        
        # 4. Do all traits have valid categories?
        for trait_name, trait in schema.traits.items():
            try:
                # This will fail if category is invalid
                _ = TraitCategory(trait.category)
                results.append((f"trait.{trait_name}.category", True, "Valid"))
            except ValueError:
                results.append((
                    f"trait.{trait_name}.category", 
                    False, 
                    f"Invalid category: {trait.category}"
                ))
        
        # 5. Does domain have required attributes?
        for attr in ["domain_id", "display_name", "domain_type"]:
            if hasattr(domain, attr):
                results.append((f"has_{attr}", True, getattr(domain, attr)))
            else:
                results.append((f"has_{attr}", False, f"Missing {attr}"))
        
        passed = all(r[1] for r in results)
        return ProbeResult(passed=passed, checks=results)
```

### Example Scenario

```python
# integration/scenarios/user_journeys/onboarding/genesis_completion.py

from integration.scenarios.base import Scenario, ScenarioResult, Step
from integration.assertions import responds_within, emits_event, updates_state

class GenesisCompletionScenario(Scenario):
    """
    Tests complete Genesis profiling flow from start to finish.
    
    This runs against the LIVE API and agents.
    """
    
    id = "user_journeys.onboarding.genesis_completion"
    description = "Complete Genesis profiling from awakening to activation"
    
    async def execute(self) -> ScenarioResult:
        steps = []
        
        # Step 1: Start new session
        session = await self.api.post("/chat/", json={"message": ""})
        steps.append(Step(
            name="start_session",
            passed=session.status_code == 200,
            details={"session_id": session.json().get("session_id")}
        ))
        
        session_id = session.json()["session_id"]
        
        # Step 2: Verify opening message has generative UI
        opening = session.json()
        steps.append(Step(
            name="opening_has_components",
            passed=len(opening.get("components", [])) > 0,
            details={"component_count": len(opening.get("components", []))}
        ))
        
        # Step 3: Respond to first question
        response1 = await self.api.post("/chat/", json={
            "message": "I feel most alive when I'm creating something new",
            "session_id": session_id
        })
        steps.append(Step(
            name="first_response",
            passed=response1.status_code == 200,
            assertion=responds_within(response1, max_ms=5000)
        ))
        
        # Step 4: Continue through phases (simplified)
        for i in range(5):
            resp = await self.api.post("/chat/", json={
                "message": f"Test response {i}",
                "session_id": session_id
            })
            steps.append(Step(
                name=f"conversation_turn_{i}",
                passed=resp.status_code == 200
            ))
        
        # Step 5: Check Digital Twin was updated
        profile = await self.get_digital_twin(session_id)
        steps.append(Step(
            name="digital_twin_updated",
            passed=len(profile.get("traits", {})) > 0,
            details={"trait_count": len(profile.get("traits", {}))}
        ))
        
        # Step 6: Verify events were emitted
        events = await self.get_events(session_id)
        steps.append(Step(
            name="events_emitted",
            passed=any(e["type"] == "trait_detected" for e in events),
            assertion=emits_event("trait_detected")
        ))
        
        return ScenarioResult(
            passed=all(s.passed for s in steps),
            steps=steps
        )
```

### API Endpoint for Live Testing

```python
# integration/runners/api/router.py

from fastapi import APIRouter
from integration import IntegrationCore

router = APIRouter(prefix="/integration", tags=["integration"])
core = IntegrationCore()

@router.get("/probes")
async def list_probes():
    """List all available probes."""
    return {"probes": core.probes.list_all()}

@router.get("/scenarios")
async def list_scenarios():
    """List all available scenarios."""
    return {"scenarios": core.scenarios.list_all()}

@router.post("/run/probe/{probe_id}")
async def run_probe(probe_id: str):
    """Run a specific probe against live system."""
    result = await core.run_probe(probe_id)
    return result.to_dict()

@router.post("/run/scenario/{scenario_id}")
async def run_scenario(scenario_id: str):
    """Run a specific scenario against live system."""
    result = await core.run_scenario(scenario_id)
    return result.to_dict()

@router.post("/run/all")
async def run_all(filter: Optional[str] = None):
    """Run all tests, optionally filtered."""
    report = await core.run_all(filter=filter)
    return report.to_dict()

@router.get("/report/latest")
async def get_latest_report():
    """Get the most recent test report."""
    return core.reports.get_latest()

@router.get("/coverage")
async def get_coverage():
    """Get test coverage analysis."""
    return core.reports.get_coverage()
```

### CLI for Development

```bash
# Run all probes for domains
python -m integration.cli run --filter "probes.domains.*"

# Run specific scenario
python -m integration.cli run --scenario "user_journeys.onboarding.genesis_completion"

# Watch mode - auto-run tests when files change
python -m integration.cli watch

# Generate coverage report
python -m integration.cli coverage

# Output:
# ┌─────────────────────────────────────────────────────────┐
# │                  INTEGRATION TEST REPORT                 │
# ├─────────────────────────────────────────────────────────┤
# │ Probes:     42/42 passed ✓                              │
# │ Scenarios:  12/12 passed ✓                              │
# │ Coverage:   87% of components tested                    │
# │                                                         │
# │ Untested:                                               │
# │ - domains.finance.goals (no probe)                      │
# │ - awareness.correlation (no probe)                      │
# └─────────────────────────────────────────────────────────┘
```

---

## ✅ COMPLETE CAPABILITY MATRIX

| Capability | Location | Purpose |
|------------|----------|---------|
| **Unified Query** | `awareness/query/` | Query ANY data with single interface |
| **Real-Time Events** | `awareness/events/` | Subscribe to system events |
| **Global State** | `awareness/state/` | Snapshot entire system |
| **Notifications** | `awareness/notifications/` | Push to user anywhere |
| **System Introspection** | `awareness/introspection/` | What exists, what can it do |
| **Cross-Domain Correlation** | `awareness/correlation/` | Find patterns across domains |
| **Live Probes** | `integration/probes/` | Test individual components |
| **E2E Scenarios** | `integration/scenarios/` | Test complete user flows |
| **Test Runners** | `integration/runners/` | CLI, API, scheduled, watch |
| **Plugin System** | `plugins/` | Hot-load new capabilities |
| **Observability** | `observability/` | Metrics, traces, logs |

---

## 🚀 THE COMPLETE PICTURE

With this addendum, the system now has:

1. ✅ **Sovereign Agent** can query ANYTHING via Unified Query Interface
2. ✅ **Real-Time Sync** via Global Event Bus
3. ✅ **Notifications** can appear ANYWHERE via Notification System
4. ✅ **Generative UI** in any context via Component System
5. ✅ **Live Testing** that works against ACTUAL code
6. ✅ **Full Observability** with metrics and traces
7. ✅ **Plugin Architecture** for runtime extensibility
8. ✅ **Cross-Domain Awareness** via Correlation Engine

All following the **True Fractal Pattern** where every piece is:
- Independently addressable
- Infinitely extensible
- Has clean separation of concerns
- Auto-discovered via registries
