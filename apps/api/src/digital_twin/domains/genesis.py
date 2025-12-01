"""
Genesis Domain - Digital Twin Domain for User Profiling

This domain defines the schema and operations for the Genesis
profiling system. It maps the ProfileRubric structure to the
new trait-based system.

@module GenesisDomain
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .base import BaseDomain, DomainSchema, TraitSchema
from .registry import DomainRegistry
from .core_types import DomainType, DomainCapability, CoreDomainId
from ..traits import TraitCategory, TraitFramework
from ..access import QueryResult


@DomainRegistry.register
class GenesisDomain(BaseDomain):
    """
    Domain for Genesis profiling system.
    
    Handles:
    - Human Design traits (type, strategy, authority, profile, channels)
    - Jungian traits (dominant function, shadow, stack)
    - Somatic patterns (body awareness, energy patterns)
    - Core patterns (values, fears, desires, purpose)
    """
    
    # Domain Identity
    domain_id = CoreDomainId.GENESIS
    display_name = "Genesis"
    description = "User profiling and Digital Twin construction"
    icon = "🔮"
    version = "2.0.0"
    priority = 100  # Highest priority - profiling is foundational
    
    # Classification
    domain_type = DomainType.CORE
    is_core = True
    
    # Capabilities
    capabilities = {
        DomainCapability.READ_TRAITS,
        DomainCapability.WRITE_TRAITS,
        DomainCapability.DETECT_PATTERNS,
        DomainCapability.GENERATE_INSIGHTS,
        DomainCapability.SYNTHESIZE,
    }
    
    # Legacy compatibility
    name = "genesis"
    
    def get_schema(self) -> DomainSchema:
        """Return the schema for Genesis domain."""
        schema = DomainSchema(domain_id=self.domain_id)
        
        # =====================================================================
        # HUMAN DESIGN TRAITS
        # =====================================================================
        
        schema.add_trait(TraitSchema(
            name="hd_type",
            display_name="Human Design Type",
            description="Your Human Design Type (energy signature)",
            value_type="enum",
            enum_options=["Generator", "Manifesting Generator", "Projector", "Manifestor", "Reflector"],
            category=TraitCategory.ENERGY,
            frameworks=[TraitFramework.HUMAN_DESIGN],
            is_required=True,
            priority=100,
            icon="⚡",
        ))
        
        schema.add_trait(TraitSchema(
            name="hd_strategy",
            display_name="Human Design Strategy",
            description="Your correct strategy for making decisions",
            value_type="enum",
            enum_options=["Wait to Respond", "Wait for the Invitation", "Inform Before Acting", "Wait a Lunar Cycle"],
            category=TraitCategory.BEHAVIOR,
            frameworks=[TraitFramework.HUMAN_DESIGN],
            priority=95,
            icon="🎯",
        ))
        
        schema.add_trait(TraitSchema(
            name="hd_authority",
            display_name="Human Design Authority",
            description="Your inner authority for decision-making",
            value_type="enum",
            enum_options=["Emotional (Solar Plexus)", "Sacral", "Splenic", "Self-Projected", "Ego Manifested", "Ego Projected", "Mental (Environmental)", "Lunar"],
            category=TraitCategory.COGNITION,
            frameworks=[TraitFramework.HUMAN_DESIGN],
            priority=90,
            icon="🧭",
        ))
        
        schema.add_trait(TraitSchema(
            name="hd_profile",
            display_name="Human Design Profile",
            description="Your profile archetype (line combinations)",
            value_type="enum",
            enum_options=["1/3", "1/4", "2/4", "2/5", "3/5", "3/6", "4/6", "4/1", "5/1", "5/2", "6/2", "6/3"],
            category=TraitCategory.ARCHETYPE,
            frameworks=[TraitFramework.HUMAN_DESIGN],
            priority=85,
            icon="🎭",
        ))
        
        schema.add_trait(TraitSchema(
            name="hd_definition",
            display_name="Definition Type",
            description="How your centers are connected",
            value_type="enum",
            enum_options=["Single Definition", "Split Definition", "Triple Split", "Quadruple Split", "No Definition"],
            category=TraitCategory.ENERGY,
            frameworks=[TraitFramework.HUMAN_DESIGN],
            priority=80,
            icon="🔗",
        ))
        
        # =====================================================================
        # JUNGIAN / MBTI TRAITS
        # =====================================================================
        
        schema.add_trait(TraitSchema(
            name="jung_dominant",
            display_name="Dominant Function",
            description="Your dominant cognitive function",
            value_type="enum",
            enum_options=["Ni", "Ne", "Si", "Se", "Ti", "Te", "Fi", "Fe"],
            category=TraitCategory.COGNITION,
            frameworks=[TraitFramework.JUNGIAN],
            priority=75,
            icon="🧠",
        ))
        
        schema.add_trait(TraitSchema(
            name="mbti_type",
            display_name="MBTI Type",
            description="Your MBTI personality type",
            value_type="enum",
            enum_options=["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP", "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"],
            category=TraitCategory.PERSONALITY,
            frameworks=[TraitFramework.MBTI],
            priority=70,
            icon="🏷️",
        ))
        
        # =====================================================================
        # CORE PATTERNS
        # =====================================================================
        
        schema.add_trait(TraitSchema(
            name="core_values",
            display_name="Core Values",
            description="Your fundamental personal values",
            value_type="list",
            category=TraitCategory.VALUE,
            frameworks=[TraitFramework.CORE_PATTERNS],
            priority=65,
            icon="💎",
        ))
        
        schema.add_trait(TraitSchema(
            name="core_fears",
            display_name="Core Fears",
            description="Deep-rooted fears and avoidances",
            value_type="list",
            category=TraitCategory.EMOTION,
            frameworks=[TraitFramework.CORE_PATTERNS],
            priority=60,
            icon="😰",
        ))
        
        schema.add_trait(TraitSchema(
            name="core_desires",
            display_name="Core Desires",
            description="Deep-rooted aspirations and wants",
            value_type="list",
            category=TraitCategory.VALUE,
            frameworks=[TraitFramework.CORE_PATTERNS],
            priority=55,
            icon="✨",
        ))
        
        # =====================================================================
        # BEHAVIORAL PATTERNS
        # =====================================================================
        
        schema.add_trait(TraitSchema(
            name="decision_style",
            display_name="Decision Style",
            description="How you typically make decisions",
            value_type="string",
            category=TraitCategory.BEHAVIOR,
            frameworks=[TraitFramework.BEHAVIORAL_PATTERNS],
            priority=50,
            icon="🤔",
        ))
        
        schema.add_trait(TraitSchema(
            name="communication_style",
            display_name="Communication Style",
            description="How you typically communicate",
            value_type="string",
            category=TraitCategory.BEHAVIOR,
            frameworks=[TraitFramework.BEHAVIORAL_PATTERNS],
            priority=45,
            icon="💬",
        ))
        
        # =====================================================================
        # META / COMPLETION
        # =====================================================================
        
        schema.add_trait(TraitSchema(
            name="profiling_phase",
            display_name="Profiling Phase",
            description="Current phase in the profiling journey",
            value_type="enum",
            enum_options=["awakening", "excavation", "mapping", "synthesis", "activation"],
            category=TraitCategory.CONTEXT,
            priority=10,
            icon="📍",
        ))
        
        schema.add_trait(TraitSchema(
            name="completion_percentage",
            display_name="Completion",
            description="Overall profiling completion",
            value_type="scale",
            scale_min=0.0,
            scale_max=1.0,
            category=TraitCategory.CONTEXT,
            priority=5,
            icon="📊",
        ))
        
        return schema
    
    async def query(self, params: Dict[str, Any]) -> QueryResult:
        """
        Query Genesis domain data.
        
        Special queries:
        - type: "summary" - Get a profile summary
        - type: "completion" - Get completion status
        - type: "frameworks" - Get data grouped by framework
        """
        query_type = params.get("type", "default")
        
        if query_type == "summary":
            return await self._get_summary(params)
        elif query_type == "completion":
            return await self._get_completion(params)
        elif query_type == "frameworks":
            return await self._get_by_frameworks(params)
        
        return QueryResult.empty()
    
    async def _get_summary(self, params: Dict[str, Any]) -> QueryResult:
        """Get a summary of the Genesis profile."""
        from ..access import get_twin_accessor
        
        accessor = await get_twin_accessor()
        traits = await accessor.get_all(domain="genesis")
        
        summary = {
            "hd_type": traits.get("hd_type", {}).value if "hd_type" in traits else None,
            "hd_strategy": traits.get("hd_strategy", {}).value if "hd_strategy" in traits else None,
            "hd_authority": traits.get("hd_authority", {}).value if "hd_authority" in traits else None,
            "hd_profile": traits.get("hd_profile", {}).value if "hd_profile" in traits else None,
            "jung_dominant": traits.get("jung_dominant", {}).value if "jung_dominant" in traits else None,
            "mbti_type": traits.get("mbti_type", {}).value if "mbti_type" in traits else None,
            "energy_pattern": traits.get("energy_pattern", {}).value if "energy_pattern" in traits else None,
            "phase": traits.get("profiling_phase", {}).value if "profiling_phase" in traits else "awakening",
            "completion": traits.get("completion_percentage", {}).value if "completion_percentage" in traits else 0.0,
        }
        
        return QueryResult.single(summary)
    
    async def _get_completion(self, params: Dict[str, Any]) -> QueryResult:
        """Get completion status for each framework."""
        from ..access import get_twin_accessor
        
        accessor = await get_twin_accessor()
        traits = await accessor.get_all(domain="genesis")
        
        schema = self.get_schema()
        
        # Group traits by framework
        frameworks = {}
        for trait_schema in schema.traits:
            fw = trait_schema.framework.value if trait_schema.framework else "misc"
            if fw not in frameworks:
                frameworks[fw] = {"required": 0, "completed": 0, "traits": []}
            
            frameworks[fw]["traits"].append(trait_schema.name)
            if trait_schema.is_required:
                frameworks[fw]["required"] += 1
            
            # Check if trait exists with sufficient confidence
            if trait_schema.name in traits:
                trait = traits[trait_schema.name]
                if trait.confidence >= 0.6:  # Medium confidence threshold
                    frameworks[fw]["completed"] += 1
        
        # Calculate percentages
        for fw in frameworks:
            total = len(frameworks[fw]["traits"])
            completed = frameworks[fw]["completed"]
            frameworks[fw]["percentage"] = completed / total if total > 0 else 0
        
        return QueryResult.single(frameworks)
    
    async def _get_by_frameworks(self, params: Dict[str, Any]) -> QueryResult:
        """Get traits grouped by framework."""
        from ..access import get_twin_accessor
        
        accessor = await get_twin_accessor()
        traits = await accessor.get_all(domain="genesis")
        
        schema = self.get_schema()
        
        # Group by framework
        grouped = {}
        for trait_schema in schema.traits:
            fw = trait_schema.framework.value if trait_schema.framework else "misc"
            if fw not in grouped:
                grouped[fw] = {}
            
            if trait_schema.name in traits:
                trait = traits[trait_schema.name]
                grouped[fw][trait_schema.name] = {
                    "value": trait.value,
                    "confidence": trait.confidence
                }
        
        return QueryResult.single(grouped)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get domain summary."""
        schema = self.get_schema()
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "trait_count": len(schema.traits),
            "frameworks": list(set(
                t.framework.value for t in schema.traits if t.framework
            ))
        }
