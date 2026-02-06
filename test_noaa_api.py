import asyncio

import aiohttp


async def test():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://services.swpc.noaa.gov/json/planetary_k_index_1m.json') as r:
            data = await r.json()
            print("Latest Kp data:", data[-1] if data else "No data")

        async with session.get('https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json') as r:
            mag_data = await r.json()
            print("Mag data lines:", len(mag_data))
            print("Latest mag:", mag_data[-1] if mag_data else "No data")

asyncio.run(test())
