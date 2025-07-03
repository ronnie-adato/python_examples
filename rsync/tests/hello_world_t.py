import asyncio
from pathlib import Path


async def run_rsync_mock(idx):
    hello_world_path = Path(__file__).parent / 'hello_world.py'
    cmd = ['python3', '-u', hello_world_path.absolute()]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    prefix = f'[src{idx+1}] '
    if process.stdout is not None:
        print(f'{prefix}', end='')
        while True:
            b = await process.stdout.read(1)
            if not b:
                break
            print(f'{b.decode().replace('\n', f'\n{prefix}')}', end='')
    retcode = await process.wait()
    return retcode


async def print_to_stdout():
    while len(asyncio.all_tasks()) > 1:
        print(
            f'waiting for rsync to finish... count: {len(asyncio.all_tasks())}')
        await asyncio.sleep(.5)


async def main():
    t = asyncio.get_event_loop().time()

    count = 10
    for idx in range(count):
        asyncio.create_task(run_rsync_mock(idx=idx))
    await print_to_stdout()  # Wait until all rsync_mock jobs are done
    t = asyncio.get_event_loop().time() - t
    print(f'All rsync jobs completed in {t:.2f} seconds.')


if __name__ == '__main__':
    asyncio.run(main())
