#!/usr/bin/env python3
"""
Test Script - Three Core Modules

Manually test Astrology, Human Design, and Numerology modules
working together with/without birth time.

Usage:
    python src/scripts/test_three_modules.py

    # Or with command line args:
    python src/scripts/test_three_modules.py --name "John Doe" --date 1990-05-15 --time 14:30 --location "San Francisco, CA"
"""
import argparse
import asyncio
import sys
from datetime import date
from datetime import time as dt_time
from pathlib import Path
from typing import Optional

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from app.core.utils.geocoding import geocode_location
from app.modules.calculation.astrology.brain.calculator import calculate_natal_chart
from app.modules.calculation.human_design.brain.calculator import HumanDesignCalculator
from app.modules.calculation.numerology.brain.calculator import NumerologyCalculator
from app.modules.calculation.numerology.brain.interpreter import NumerologyInterpreter


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def get_birth_data_interactive():
    """Get birth data from user input"""
    print_section("GUTTERS - Birth Data Entry")

    # Name
    name = input("Enter full name: ").strip()
    if not name:
        name = "Test User"
        print(f"  Using default: {name}")

    # Birth date
    print("\nEnter birth date:")
    year = int(input("  Year (YYYY): ") or "1990")
    month = int(input("  Month (1-12): ") or "5")
    day = int(input("  Day (1-31): ") or "15")
    birth_date = date(year, month, day)

    # Birth time (optional)
    has_time = input("\nDo you know your birth time? (y/n): ").strip().lower()
    birth_time = None

    if has_time == 'y':
        hour = int(input("  Hour (0-23): ") or "12")
        minute = int(input("  Minute (0-59): ") or "0")
        birth_time = dt_time(hour, minute)
    else:
        print("\n⚠️  Birth time unknown - solar/partial chart will be calculated")

    # Birth location
    birth_location = input("\nEnter birth location (city, state/country): ").strip()
    if not birth_location:
        birth_location = "San Francisco, CA"
        print(f"  Using default: {birth_location}")

    return name, birth_date, birth_time, birth_location


def get_birth_data_from_args(args):
    """Get birth data from command line arguments"""
    name = args.name

    # Parse date
    parts = args.date.split('-')
    birth_date = date(int(parts[0]), int(parts[1]), int(parts[2]))

    # Parse time if provided
    birth_time = None
    if args.time:
        t_parts = args.time.split(':')
        birth_time = dt_time(int(t_parts[0]), int(t_parts[1]))

    birth_location = args.location

    return name, birth_date, birth_time, birth_location


def geocode_birth_location(location_str: str) -> dict:
    """Geocode a location string"""
    print(f"\n🌍 Geocoding '{location_str}'...")
    geo_result = geocode_location(location_str)

    if not geo_result:
        raise ValueError(f"Could not geocode location: {location_str}")

    print(f"✓ Found: {geo_result['address']}")
    print(f"  Coordinates: ({geo_result['latitude']:.4f}, {geo_result['longitude']:.4f})")
    print(f"  Timezone: {geo_result['timezone']}")

    return geo_result


def test_astrology(name: str, birth_date: date, birth_time: Optional[dt_time],
                   latitude: float, longitude: float, timezone: str):
    """Test astrology module"""
    print_section("ASTROLOGY MODULE")

    print("🔮 Calculating natal chart...")
    chart = calculate_natal_chart(
        name=name,
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone
    )

    print("\n📊 Chart Data:")
    print(f"  Accuracy: {chart['accuracy']}")
    if chart.get('note'):
        print(f"  Note: {chart['note']}")

    # Find planet data
    sun = next((p for p in chart['planets'] if p['name'] == 'Sun'), None)
    moon = next((p for p in chart['planets'] if p['name'] == 'Moon'), None)
    mercury = next((p for p in chart['planets'] if p['name'] == 'Mercury'), None)
    venus = next((p for p in chart['planets'] if p['name'] == 'Venus'), None)
    mars = next((p for p in chart['planets'] if p['name'] == 'Mars'), None)

    if sun:
        print(f"\n☀️  Sun: {sun['sign']} {sun['degree']:.2f}°")
    if moon:
        print(f"🌙 Moon: {moon['sign']} {moon['degree']:.2f}°")
    if mercury:
        print(f"☿️  Mercury: {mercury['sign']} {mercury['degree']:.2f}°")
    if venus:
        print(f"♀️  Venus: {venus['sign']} {venus['degree']:.2f}°")
    if mars:
        print(f"♂️  Mars: {mars['sign']} {mars['degree']:.2f}°")

    if chart['accuracy'] == 'full' and chart.get('ascendant'):
        print(f"\n🔺 Rising: {chart['ascendant']['sign']} {chart['ascendant']['degree']:.2f}°")
        print("\n🏠 Houses:")
        for house in chart['houses'][:3]:  # First 3 houses
            print(f"  House {house['number']}: {house['sign']}")

    print(f"\n🔥 Elements: {chart['elements']}")
    print(f"📐 Modalities: {chart['modalities']}")

    return chart


def test_human_design(name: str, birth_date: date, birth_time: Optional[dt_time],
                      latitude: float, longitude: float, timezone: str):
    """Test Human Design module with full feature display"""
    print_section("HUMAN DESIGN MODULE")

    print("⚡ Calculating bodygraph...")
    calculator = HumanDesignCalculator()
    chart = calculator.calculate_chart(
        name=name,
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone
    )

    print("\n📊 Chart Data:")
    print(f"  Type: {chart.type}")
    print(f"  Strategy: {chart.strategy}")
    print(f"  Authority: {chart.authority}")
    print(f"  Profile: {chart.profile}")
    print(f"  Definition: {chart.definition or 'N/A'}")
    print(f"  Accuracy: {chart.accuracy}")
    if chart.note:
        print(f"  Note: {chart.note}")

    # Signature and Not-Self (new features)
    if chart.signature:
        print(f"\n✨ Signature (Aligned): {chart.signature}")
    if chart.not_self:
        print(f"⚠️  Not-Self (Misaligned): {chart.not_self}")

    # Incarnation Cross (new feature)
    if chart.incarnation_cross:
        print(f"\n🎯 Incarnation Cross: {chart.incarnation_cross}")

    print(f"\n🟢 Defined Centers ({len(chart.defined_centers)}):")
    for center in chart.defined_centers:
        print(f"  • {center}")

    print(f"\n⚪ Undefined Centers ({len(chart.undefined_centers)}):")
    for center in chart.undefined_centers:
        print(f"  • {center}")

    if chart.accuracy == "full":
        print("\n🎯 Key Gates (Personality):")
        for gate in chart.personality_gates[:5]:
            sub_line = f" (Color:{gate.color} Tone:{gate.tone} Base:{gate.base})" if gate.color else ""
            print(f"  • {gate.planet}: Gate {gate.gate}.{gate.line}{sub_line}")

        print("\n🎯 Key Gates (Design):")
        for gate in chart.design_gates[:5]:
            sub_line = f" (Color:{gate.color} Tone:{gate.tone} Base:{gate.base})" if gate.color else ""
            print(f"  • {gate.planet}: Gate {gate.gate}.{gate.line}{sub_line}")

        defined_channels = [c for c in chart.channels if c.defined]
        if defined_channels:
            print(f"\n🔗 Defined Channels ({len(defined_channels)}):")
            for channel in defined_channels[:5]:
                print(f"  • {channel.name}: {channel.gates[0]}-{channel.gates[1]}")
                if channel.theme:
                    print(f"    └─ {channel.theme}")

    # Probabilistic type info
    if chart.type_confidence is not None:
        print(f"\n📊 Type Confidence: {chart.type_confidence:.0%}")
        if chart.type_probabilities:
            print("   Type Distribution:")
            for tp in chart.type_probabilities:
                print(f"    • {tp.value}: {tp.probability:.1%} ({tp.sample_count} hours)")

    return chart


def test_numerology(name: str, birth_date: date):
    """Test numerology module"""
    print_section("NUMEROLOGY MODULE")

    print("🔢 Calculating numerology chart...")
    calculator = NumerologyCalculator()
    chart = calculator.calculate_chart(
        name=name,
        birth_date=birth_date
    )

    print("\n📊 Chart Data:")
    print(f"  Life Path: {chart.life_path}{'*' if chart.is_master_life_path else ''}")
    print(f"  Expression: {chart.expression}{'*' if chart.is_master_expression else ''}")
    print(f"  Soul Urge: {chart.soul_urge}{'*' if chart.is_master_soul_urge else ''}")
    print(f"  Personality: {chart.personality}")
    print(f"  Birthday: {chart.birthday}")

    if chart.master_numbers:
        print(f"\n✨ Master Numbers: {', '.join(map(str, chart.master_numbers))}")

    if chart.karmic_debt_numbers:
        print(f"⚠️  Karmic Debt: {', '.join(map(str, chart.karmic_debt_numbers))}")

    # Basic interpretation (no LLM needed)
    interpreter = NumerologyInterpreter()
    insights = asyncio.get_event_loop().run_until_complete(
        interpreter.interpret_chart(chart)
    )

    print("\n" + "─"*80)
    print(insights[:800] + "..." if len(insights) > 800 else insights)
    print("─"*80)

    return chart


def generate_synthesis_summary(name: str, astro_chart: dict, hd_chart, num_chart,
                               has_birth_time: bool):
    """Generate a simple synthesis summary"""
    print_section("SYNTHESIS SUMMARY")

    sun = next((p for p in astro_chart['planets'] if p['name'] == 'Sun'), None)
    moon = next((p for p in astro_chart['planets'] if p['name'] == 'Moon'), None)

    print(f"📋 Profile Summary for {name}:\n")

    print("🔮 ASTROLOGY:")
    if sun:
        print(f"   Sun Sign: {sun['sign']}")
    if moon:
        print(f"   Moon Sign: {moon['sign']}")
    if astro_chart['accuracy'] == 'full' and astro_chart.get('ascendant'):
        print(f"   Rising: {astro_chart['ascendant']['sign']}")
    print(f"   Accuracy: {astro_chart['accuracy']}")

    print("\n⚡ HUMAN DESIGN:")
    print(f"   Type: {hd_chart.type}")
    print(f"   Strategy: {hd_chart.strategy}")
    print(f"   Authority: {hd_chart.authority}")
    print(f"   Profile: {hd_chart.profile}")
    print(f"   Accuracy: {hd_chart.accuracy}")

    print("\n🔢 NUMEROLOGY:")
    print(f"   Life Path: {num_chart.life_path}")
    print(f"   Expression: {num_chart.expression}")
    print(f"   Soul Urge: {num_chart.soul_urge}")
    print("   Accuracy: full (doesn't require birth time)")

    print("\n" + "─"*80)
    print("KEY INTEGRATION POINTS:")
    print("─"*80)

    # Simple synthesis bullet points
    print(f"\n• As a {hd_chart.type}, your strategy is to {hd_chart.strategy.lower()}")
    print(f"• Your {sun['sign'] if sun else 'Sun'} Sun expresses through Life Path {num_chart.life_path}")
    print(f"• Soul Urge {num_chart.soul_urge} aligns with your {hd_chart.authority}")

    if not has_birth_time:
        print("\n⚠️  Note: For full accuracy in Astrology and Human Design,")
        print("   consider providing your exact birth time.")


def main():
    """Main test flow"""
    parser = argparse.ArgumentParser(description="Test three GUTTERS modules")
    parser.add_argument('--name', type=str, help='Full name')
    parser.add_argument('--date', type=str, help='Birth date (YYYY-MM-DD)')
    parser.add_argument('--time', type=str, help='Birth time (HH:MM)')
    parser.add_argument('--location', type=str, help='Birth location')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Run in interactive mode')

    args = parser.parse_args()

    try:
        # Get birth data
        if args.interactive or not all([args.name, args.date, args.location]):
            name, birth_date, birth_time, birth_location = get_birth_data_interactive()
        else:
            name, birth_date, birth_time, birth_location = get_birth_data_from_args(args)

        # Geocode location
        geo_result = geocode_birth_location(birth_location)
        latitude = geo_result['latitude']
        longitude = geo_result['longitude']
        timezone = geo_result['timezone']

        # Test each module
        astro_chart = test_astrology(name, birth_date, birth_time, latitude, longitude, timezone)
        hd_chart = test_human_design(name, birth_date, birth_time, latitude, longitude, timezone)
        num_chart = test_numerology(name, birth_date)

        # Generate synthesis summary
        generate_synthesis_summary(name, astro_chart, hd_chart, num_chart,
                                   has_birth_time=birth_time is not None)

        print_section("✅ ALL TESTS COMPLETE")
        print("All three modules calculated successfully!")
        print("\nAccuracy Summary:")
        print(f"  • Astrology: {astro_chart['accuracy']}")
        print(f"  • Human Design: {hd_chart.accuracy}")
        print("  • Numerology: full (always)")

        if birth_time:
            print(f"\n📍 Birth Time: {birth_time.strftime('%H:%M')}")
        else:
            print("\n⚠️  Birth Time: Unknown (partial calculations used)")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
