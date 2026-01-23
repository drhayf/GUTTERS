#!/usr/bin/env python3
"""
Interactive Genesis Conversation Test

Tests the full conversational flow:
1. Create hypotheses from mock uncertainties
2. Start conversation session
3. Answer probes interactively
4. See fields get confirmed
5. Get session summary

Usage:
    cd src
    python -m scripts.test_genesis_conversation

Or:
    python src/scripts/test_genesis_conversation.py
"""

import asyncio
from datetime import date

# Add src to path if running directly
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


async def main():
    print("🌟 GENESIS CONVERSATIONAL REFINEMENT TEST\n")
    print("=" * 60)
    
    # Import Genesis components
    from app.modules.intelligence.genesis.engine import GenesisEngine
    from app.modules.intelligence.genesis.session import GenesisSessionManager
    from app.modules.intelligence.genesis.uncertainty import (
        UncertaintyDeclaration,
        UncertaintyField,
    )
    from app.modules.intelligence.genesis.probes import ProbeType, ProbeResponse
    from app.modules.intelligence.genesis.strategies import StrategyRegistry
    
    # Initialize
    StrategyRegistry.initialize_defaults()
    
    # Create mock uncertainty declaration (simulating probabilistic calculation)
    print("📝 Simulating birth data submission (no time)...")
    
    declaration = UncertaintyDeclaration(
        module="astrology",
        user_id=1,
        session_id="test-session",
        source_accuracy="probabilistic",
        fields=[
            UncertaintyField(
                field="rising_sign",
                module="astrology",
                candidates={
                    "Leo": 0.25,
                    "Virgo": 0.25,
                    "Libra": 0.25,
                    "Scorpio": 0.25,
                },
                confidence_threshold=0.80,
                refinement_strategies=["morning_routine", "first_impression"],
            )
        ],
    )
    
    # Initialize engine with hypotheses
    engine = GenesisEngine()
    hypotheses = await engine.initialize_from_uncertainties([declaration])
    
    print(f"\n📊 Created {len(hypotheses)} hypotheses:")
    for h in hypotheses:
        print(f"   • {h.field}={h.suspected_value} ({h.confidence:.0%})")
    
    # Create session
    manager = GenesisSessionManager()
    session = await manager.create_session(
        user_id=1,
        hypothesis_ids=[h.id for h in hypotheses]
    )
    
    print(f"\n🤖 Genesis Session Started: {session.session_id}")
    print(f"   Max probes: {session.max_probes_per_session}")
    
    # Conversation loop
    turn = 1
    conversation_active = True
    
    while conversation_active and turn <= 5:  # Limit to 5 turns for demo
        print(f"\n{'='*60}")
        print(f"TURN {turn}")
        print(f"{'='*60}\n")
        
        # Get next probe
        probe = await manager.get_next_probe(session, engine)
        
        if not probe:
            print("No more probes available.")
            break
        
        # Show probe
        print(f"🔮 QUESTION ({probe.strategy_used}):")
        print(f"   {probe.question}")
        
        if probe.probe_type == ProbeType.BINARY_CHOICE and probe.options:
            print(f"\n   Options:")
            for i, option in enumerate(probe.options):
                print(f"   [{i}] {option}")
            
            # Get user input
            while True:
                try:
                    user_input = input("\n   Your choice (0 or 1, or 'q' to quit): ").strip()
                    if user_input.lower() == 'q':
                        conversation_active = False
                        break
                    choice = int(user_input)
                    if choice in (0, 1):
                        break
                    print("   Please enter 0 or 1")
                except ValueError:
                    print("   Please enter a number")
            
            if not conversation_active:
                break
            
            response = ProbeResponse(
                probe_id=probe.id,
                response_type=ProbeType.BINARY_CHOICE,
                selected_option=choice,
            )
        else:
            # For non-binary, just simulate a response
            print("\n   (Simulating response...)")
            response = ProbeResponse(
                probe_id=probe.id,
                response_type=probe.probe_type,
                reflection_text="I resonate with that.",
            )
        
        # Process response
        result = await manager.process_response(session, response, engine)
        
        # Show confidence updates
        print(f"\n📈 Confidence updates:")
        for h in engine.get_active_hypotheses(1):
            status = "→" if h.confidence < 0.80 else "✓"
            print(f"   {status} {h.suspected_value}: {h.confidence:.0%}")
        
        # Show confirmations
        if result["confirmations"]:
            print(f"\n✅ CONFIRMED:")
            for conf in result["confirmations"]:
                print(f"   {conf['field']} = {conf['confirmed_value']} ({conf['confidence']:.0%})")
        
        # Check if complete
        if result["session_complete"]:
            print(f"\n🎉 Session complete!")
            if result["summary"]:
                print(f"\n{result['summary']}")
            conversation_active = False
        else:
            turn += 1
    
    # Final summary
    if conversation_active:
        result = await manager.complete_session(session, engine, "demo_finished")
        print(f"\n{'='*60}")
        print("SESSION SUMMARY")
        print(f"{'='*60}")
        print(result["summary"])
    
    print("\n✨ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
