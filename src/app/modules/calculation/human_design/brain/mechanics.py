"""
Human Design Mechanics - Type, Authority, Definition

Verified implementation of HD mechanics from dturkuler/humandesign_api.
Clean separation of type determination, authority, and definition logic.

Key features:
- Type determination with motor-to-throat path checking
- Authority hierarchy implementation
- Definition calculation (connected components)
- Channel and center activation logic
"""
from typing import Optional
import numpy as np
from collections import defaultdict

from . import constants


class ChannelBuilder:
    """
    Builds channel and center data from gate lists.
    
    Creates bidirectional lookups for efficient querying.
    """
    
    def __init__(self):
        """Initialize channel lookup dictionaries."""
        self._build_lookup_tables()
    
    def _build_lookup_tables(self):
        """Build efficient lookup tables for channel queries."""
        # Gate to channel gate mapping (bidirectional)
        self.gate_pairs = {}
        self.gate_to_center = {}
        
        # Build from GATES_CHAKRA_DICT
        for (gate1, gate2), (center1, center2) in constants.GATES_CHAKRA_DICT.items():
            # Map gate to its channel partner
            if gate1 not in self.gate_pairs:
                self.gate_pairs[gate1] = []
            if gate2 not in self.gate_pairs:
                self.gate_pairs[gate2] = []
            
            self.gate_pairs[gate1].append(gate2)
            self.gate_pairs[gate2].append(gate1)
            
            # Map gate to center (using full names)
            self.gate_to_center[gate1] = constants.CENTER_ABBREV[center1]
            self.gate_to_center[gate2] = constants.CENTER_ABBREV[center2]
    
    def find_active_channels(
        self,
        all_gates: list[int]
    ) -> tuple[list[tuple], set[str]]:
        """
        Find all active channels from a list of activated gates.
        
        A channel is active when both gates are present.
        
        Args:
            all_gates: List of all activated gate numbers
            
        Returns:
            (list of channel tuples, set of defined center names)
        """
        gate_set = set(all_gates)
        active_channels = []
        defined_centers = set()
        
        # Check each channel definition
        for (gate1, gate2), (center1, center2) in constants.GATES_CHAKRA_DICT.items():
            if gate1 in gate_set and gate2 in gate_set:
                # Channel is active
                active_channels.append((gate1, gate2))
                
                # Both centers are now defined
                defined_centers.add(constants.CENTER_ABBREV[center1])
                defined_centers.add(constants.CENTER_ABBREV[center2])
        
        return active_channels, defined_centers
    
    def build_center_connections(
        self,
        active_channels: list[tuple]
    ) -> dict[str, set[str]]:
        """
        Build a graph of center connections from active channels.
        
        Args:
            active_channels: List of active channel tuples (gate1, gate2)
            
        Returns:
            Dict mapping center name to set of connected centers
        """
        connections = defaultdict(set)
        
        for gate1, gate2 in active_channels:
            # Get centers for these gates
            chakras = constants.GATES_CHAKRA_DICT.get((gate1, gate2))
            if not chakras:
                chakras = constants.GATES_CHAKRA_DICT.get((gate2, gate1))
            
            if chakras:
                center1 = constants.CENTER_ABBREV[chakras[0]]
                center2 = constants.CENTER_ABBREV[chakras[1]]
                
                connections[center1].add(center2)
                connections[center2].add(center1)
        
        return dict(connections)


class TypeDeterminator:
    """
    Determines HD Type from centers and channels.
    
    Verified implementation of type logic including
    motor-to-throat path detection.
    """
    
    def __init__(self, channel_builder: ChannelBuilder):
        self.channel_builder = channel_builder
    
    def is_connected(
        self,
        connections: dict[str, set[str]],
        *centers: str
    ) -> bool:
        """
        Check if centers form a connected path in sequence.
        
        Args:
            connections: Center connection graph
            centers: Sequence of centers to check
            
        Returns:
            True if path exists
        """
        if len(centers) < 2:
            return True
        
        for i in range(len(centers) - 1):
            c1 = centers[i]
            c2 = centers[i + 1]
            
            # Check if these centers are directly connected
            if c1 not in connections or c2 not in connections[c1]:
                return False
        
        return True
    
    def has_motor_to_throat(
        self,
        defined_centers: set[str],
        connections: dict[str, set[str]]
    ) -> bool:
        """
        Check if any motor center connects to Throat.
        
        Motors: Sacral, Solar Plexus, Heart, Root
        
        Args:
            defined_centers: Set of defined center names
            connections: Center connection graph
            
        Returns:
            True if motor-to-throat connection exists
        """
        # Check all possible motor-to-throat paths
        
        # 1. Sacral to Throat
        tt_sl_connected = (
            self.is_connected(connections, "Throat", "G", "Sacral") or
            self.is_connected(connections, "Throat", "Sacral")  # Direct 20-34
        )
        
        # 2. Heart to Throat
        tt_ht_connected = (
            self.is_connected(connections, "Throat", "Heart") or  # Direct 21-45
            self.is_connected(connections, "Throat", "G", "Heart") or  # Via G
            self.is_connected(connections, "Throat", "Spleen", "Heart")  # Via Spleen
        )
        
        # 3. Solar Plexus to Throat
        tt_sp_connected = (
            self.is_connected(connections, "Throat", "Solar Plexus") or  # 12-22, 35-36
            self.is_connected(connections, "Throat", "G", "Solar Plexus")
        )
        
        # 4. Root to Throat (via Spleen)
        tt_rt_connected = (
            self.is_connected(connections, "Throat", "Spleen", "Root") or
            self.is_connected(connections, "Throat", "G", "Spleen", "Root")
        )
        
        return tt_sl_connected or tt_ht_connected or tt_sp_connected or tt_rt_connected
    
    def determine_type(
        self,
        defined_centers: set[str],
        connections: dict[str, set[str]]
    ) -> dict:
        """
        Determine HD Type from centers and connections.
        
        Type hierarchy:
        1. No centers defined -> Reflector
        2. Sacral defined + motor-to-throat -> Manifesting Generator
        3. Sacral defined -> Generator
        4. Motor-to-throat -> Manifestor
        5. Default -> Projector
        
        Args:
            defined_centers: Set of defined center names
            connections: Center connection graph
            
        Returns:
            Dict with type and details
        """
        # Rule 1: No Definition = Reflector
        if not defined_centers:
            return self._build_type_result("Reflector")
        
        has_sacral = "Sacral" in defined_centers
        has_motor_throat = self.has_motor_to_throat(defined_centers, connections)
        
        # Rule 2 & 3: Sacral defined
        if has_sacral:
            if has_motor_throat:
                return self._build_type_result("Manifesting Generator")
            else:
                return self._build_type_result("Generator")
        
        # Rule 4: Motor to Throat (no Sacral)
        if has_motor_throat:
            return self._build_type_result("Manifestor")
        
        # Rule 5: Default
        return self._build_type_result("Projector")
    
    def _build_type_result(self, type_name: str) -> dict:
        """Build type result with details."""
        details = constants.TYPE_DETAILS.get(type_name, {})
        return {
            "type": type_name,
            "strategy": details.get("strategy", "Unknown"),
            "signature": details.get("signature", "Unknown"),
            "not_self": details.get("not_self", "Unknown"),
            "aura": details.get("aura", "Unknown"),
        }


class AuthorityDeterminator:
    """
    Determines Inner Authority from centers and connections.
    
    Authority hierarchy:
    1. Solar Plexus (53%)
    2. Sacral (31%)
    3. Spleen (9%)
    4. Heart (1.5%)
    5. G Center (2.5%)
    6. Lunar / No Inner (3%)
    """
    
    def __init__(self, type_determinator: TypeDeterminator):
        self.type_determinator = type_determinator
    
    def determine_authority(
        self,
        defined_centers: set[str],
        connections: dict[str, set[str]]
    ) -> dict:
        """
        Determine authority from centers and connections.
        
        Args:
            defined_centers: Set of defined center names
            connections: Center connection graph
            
        Returns:
            Dict with authority code and name
        """
        # 1. Emotional Authority (Solar Plexus defined)
        if "Solar Plexus" in defined_centers:
            return self._build_result("SP")
        
        # 2. Sacral Authority
        if "Sacral" in defined_centers:
            return self._build_result("SL")
        
        # 3. Splenic Authority
        if "Spleen" in defined_centers:
            return self._build_result("SN")
        
        # 4. Heart/Ego Authority
        if "Heart" in defined_centers:
            # Check if Heart connects to Throat (Ego-Manifested)
            if self.type_determinator.is_connected(connections, "Heart", "Throat"):
                return self._build_result("HT")
            else:
                # Ego-Projected
                return self._build_result("HT_GC")
        
        # 5. Self-Projected (G to Throat)
        if "G" in defined_centers:
            if self.type_determinator.is_connected(connections, "G", "Throat"):
                return self._build_result("GC")
        
        # 6. No centers = Reflector (Lunar)
        if not defined_centers:
            return self._build_result("lunar")
        
        # 7. Other (Mental Projector - no inner authority)
        return self._build_result("outer")
    
    def _build_result(self, code: str) -> dict:
        """Build authority result."""
        return {
            "code": code,
            "name": constants.AUTHORITY_NAMES.get(code, "Unknown"),
        }


class DefinitionCalculator:
    """
    Calculates Definition type (number of connected components).
    
    0 = No Definition (Reflector)
    1 = Single Definition
    2 = Split Definition
    3 = Triple Split
    4 = Quadruple Split
    """
    
    def calculate_definition(
        self,
        defined_centers: set[str],
        connections: dict[str, set[str]]
    ) -> dict:
        """
        Calculate definition by counting connected components.
        
        Uses graph traversal (DFS) to find islands.
        
        Args:
            defined_centers: Set of defined center names
            connections: Center connection graph
            
        Returns:
            Dict with count and name
        """
        if not defined_centers:
            return {"count": 0, "name": constants.DEFINITION_NAMES[0]}
        
        # Build adjacency for defined centers only
        graph = {c: set() for c in defined_centers}
        for center in defined_centers:
            for connected in connections.get(center, []):
                if connected in defined_centers:
                    graph[center].add(connected)
        
        # Count connected components
        visited = set()
        islands = 0
        
        for center in defined_centers:
            if center not in visited:
                islands += 1
                # DFS to mark all connected
                stack = [center]
                while stack:
                    node = stack.pop()
                    if node not in visited:
                        visited.add(node)
                        stack.extend(graph[node] - visited)
        
        return {
            "count": islands,
            "name": constants.DEFINITION_NAMES.get(islands, f"{islands}-Split Definition"),
        }


class ProfileCalculator:
    """
    Calculates Profile from Personality and Design Sun lines.
    """
    
    def calculate_profile(
        self,
        personality_sun_line: int,
        design_sun_line: int
    ) -> dict:
        """
        Calculate profile from Sun lines.
        
        Args:
            personality_sun_line: Line of Personality Sun (1-6)
            design_sun_line: Line of Design Sun (1-6)
            
        Returns:
            Dict with lines and profile name
        """
        profile_key = (personality_sun_line, design_sun_line)
        profile_name = constants.PROFILE_NAMES.get(
            profile_key,
            f"{personality_sun_line}/{design_sun_line}"
        )
        cross_type = constants.IC_CROSS_TYPE.get(profile_key, "Unknown")
        
        return {
            "personality_line": personality_sun_line,
            "design_line": design_sun_line,
            "name": profile_name,
            "cross_type": cross_type,
        }


class IncarnationCrossCalculator:
    """
    Calculates Incarnation Cross from Sun/Earth gates.
    """
    
    def calculate_cross(
        self,
        personality_sun_gate: int,
        personality_earth_gate: int,
        design_sun_gate: int,
        design_earth_gate: int,
        cross_type: str = "RAC"
    ) -> dict:
        """
        Calculate Incarnation Cross.
        
        Args:
            personality_sun_gate: Personality Sun gate
            personality_earth_gate: Personality Earth gate
            design_sun_gate: Design Sun gate
            design_earth_gate: Design Earth gate
            cross_type: RAC, JC, or LAC
            
        Returns:
            Dict with cross data
        """
        # Get cross name from personality sun gate
        cross_data = constants.INCARNATION_CROSS_DB.get(personality_sun_gate, {})
        
        # Map cross type codes
        type_key = "JC" if cross_type == "JXP" else cross_type
        cross_name = cross_data.get(type_key, f"Cross of Gate {personality_sun_gate}")
        
        return {
            "name": cross_name,
            "type": cross_type,
            "gates": {
                "personality_sun": personality_sun_gate,
                "personality_earth": personality_earth_gate,
                "design_sun": design_sun_gate,
                "design_earth": design_earth_gate,
            },
        }


# Module-level instances for convenience
_channel_builder = None
_type_determinator = None
_authority_determinator = None
_definition_calculator = None
_profile_calculator = None
_cross_calculator = None


def get_channel_builder() -> ChannelBuilder:
    global _channel_builder
    if _channel_builder is None:
        _channel_builder = ChannelBuilder()
    return _channel_builder


def get_type_determinator() -> TypeDeterminator:
    global _type_determinator
    if _type_determinator is None:
        _type_determinator = TypeDeterminator(get_channel_builder())
    return _type_determinator


def get_authority_determinator() -> AuthorityDeterminator:
    global _authority_determinator
    if _authority_determinator is None:
        _authority_determinator = AuthorityDeterminator(get_type_determinator())
    return _authority_determinator


def get_definition_calculator() -> DefinitionCalculator:
    global _definition_calculator
    if _definition_calculator is None:
        _definition_calculator = DefinitionCalculator()
    return _definition_calculator


def get_profile_calculator() -> ProfileCalculator:
    global _profile_calculator
    if _profile_calculator is None:
        _profile_calculator = ProfileCalculator()
    return _profile_calculator


def get_cross_calculator() -> IncarnationCrossCalculator:
    global _cross_calculator
    if _cross_calculator is None:
        _cross_calculator = IncarnationCrossCalculator()
    return _cross_calculator
