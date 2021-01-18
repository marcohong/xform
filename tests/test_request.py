import asyncio
import aiohttp
import threading


def run_thread():
    _loop = asyncio.new_event_loop()
    loop_thread = threading.Thread(target=start_thread_loop, args=(_loop,))
    loop_thread.setDaemon(True)
    loop_thread.start()
    ret = asyncio.run_coroutine_threadsafe(run_thread_http(_loop), _loop)
    ret.result()


async def run_thread_http(_loop):
    session = aiohttp.ClientSession()
    tasks = [process(i, session) for i in range(200, 350)]
    await asyncio.gather(*tasks, loop=_loop)
    await session.close()


def start_thread_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


async def process(num, session):
    url = (f'http://localhost:8888?id={num}&name=test{num}'
           f'&status=1&user.uid={num}&user.name=user{num}')
    async with session.get(url) as resp:
        text = await resp.text('utf-8')
        print(text)


async def main():
    run_thread()
    session = aiohttp.ClientSession()
    tasks = [process(i, session) for i in range(2, 52)]
    await asyncio.gather(*tasks)
    await session.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
