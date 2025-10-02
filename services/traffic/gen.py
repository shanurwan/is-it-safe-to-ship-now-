import os
import asyncio
import httpx

TARGET = os.getenv("TARGET", "http://traefik")
RATE = int(os.getenv("RATE", "100"))  # requests/sec


async def hit(client: httpx.AsyncClient) -> None:
    try:
        await client.get(TARGET, timeout=3.0)
    except Exception:
        # swallow errors; this is a simple firehose
        pass


async def main() -> None:
    async with httpx.AsyncClient() as client:
        while True:
            tasks = [hit(client) for _ in range(RATE)]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(1.0)


if __name__ == "__main__":
    asyncio.run(main())
