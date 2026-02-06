import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta

# Add project root to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from sqlalchemy import insert

from src.app.core.db.database import async_get_db
from src.app.models.cosmic_conditions import CosmicConditions


async def seed():
    print("Seeding High-Fidelity Telemetry (SQLAlchemy Insert Mode)...")
    async for db in async_get_db():
        try:
            # 1. Solar Storm Scenario (Last 24 hours)
            print("Generating Solar Storm Data...")
            now = datetime.now(UTC)

            for i in range(24):
                t = now - timedelta(hours=24 - i)
                progress = i / 24.0
                bz = 5.0 - (15.0 * progress)
                speed = 400 + (300 * progress)
                density = 5.0 + (10 * progress)
                kp = 2 + (5 * progress)

                data_dict = {
                    "bz": float(bz),
                    "solar_wind_speed": float(speed),
                    "solar_wind_density": float(density),
                    "kp_index": float(kp),
                    "storm_potential": "Critical" if i > 18 else "Low",
                    "shield_integrity": "CRITICAL" if i > 20 else "NOMINAL",
                }

                stmt = insert(CosmicConditions).values(
                    condition_type="solar", timestamp=t, source="SeedScript", data=data_dict
                )
                await db.execute(stmt)

            # 2. Lunar Data
            print("Generating Lunar Data...")
            lunar_dict = {
                "phase_name": "Waning Gibbous",
                "sign": "Leo",
                "is_voc": False,
                "time_until_voc_minutes": 45,
                "distance_km": 370000.0,
                "supermoon_score": 0.8,
                "illumination": 0.85,
            }
            await db.execute(
                insert(CosmicConditions).values(
                    condition_type="lunar", timestamp=now, source="SeedScript", data=lunar_dict
                )
            )

            # 3. Transits
            print("Generating Transit Data...")
            transit_dict = {
                "positions": {
                    "Mercury": {"is_retrograde": True, "speed": -0.5, "sign": "Capricorn", "degree": 14.5, "house": 3},
                    "Mars": {"is_retrograde": True, "speed": -0.1, "sign": "Leo", "degree": 28.2, "house": 5},
                    "Venus": {"is_retrograde": False, "speed": 1.2, "sign": "Aquarius", "degree": 5.0, "house": 11},
                }
            }
            await db.execute(
                insert(CosmicConditions).values(
                    condition_type="planetary", timestamp=now, source="SeedScript", data=transit_dict
                )
            )

            await db.commit()
            print("✅ Telemetry Seeded Successfully via SQLAlchemy Insert.")

        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await db.rollback()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed())
