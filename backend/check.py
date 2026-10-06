import httpx
import asyncio
async def test():
    async with httpx.AsyncClient() as c:
        r = await c.get('http://127.0.0.1:8000/api/v1/papers/1/research-summary')
        print(r.json())
asyncio.run(test())
