import os, asyncio, httpx

TARGET = os.getenv("TARGET", "http://traefik")
RATE = int(os.getenv("RATE", "100"))

async def hit(client):
    try:
        await client.get(TARGET, timeout=3)
    except Exception:
        pass

async def main():
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.gather(*[hit(client) for _ in range(RATE)], return_exceptions=True)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
