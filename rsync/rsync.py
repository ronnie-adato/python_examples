#!/usr/bin/env python3

import argparse
import logging
from logging.handlers import RotatingFileHandler
import asyncio
import sys
import tomllib


logger = logging.getLogger("rsync")


def setup_logger():
    # Load logging config from pyproject.toml
    config = {
        "level": "INFO",
        "filename": "rsync.log",
        "max_bytes": 0x10000,  # 64 KiB
        "backup_count": 0x10,  # 16 backups
        "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    }
    try:
        with open("pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
            log_cfg = pyproject.get("tool", {}).get("rsync_like", {}).get("logging", {})
            config.update({
                k: log_cfg[k] for k in config if k in log_cfg
            })
    except Exception as e:
        print(f"Warning: Could not load logging config from pyproject.toml: {e}", file=sys.stderr)
    logger.setLevel(getattr(logging, config["level"].upper(), logging.INFO))
    handler = RotatingFileHandler(
        config["filename"],
        maxBytes=int(config["max_bytes"]),
        backupCount=int(config["backup_count"])
    )
    formatter = logging.Formatter(config["format"])
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sync two directories (rsync-like).\n"
        "Any additional arguments after all --src_dst pairs are passed directly to rsync.\n"
        "Example: --src_dst src1,dst1 --src_dst src2,dst2 --progress --delete"
    )
    parser.add_argument(
        '--src_dst',
        type=lambda s: [item.strip() for item in s.split(',')],
        required=True,
        action='append',
        help='Comma-separated source and destination (must occur at least once, can be repeated: --src_dst src1,dst1 --src_dst src2,dst2). '
             'All arguments other than --src_dst are passed as extra rsync options.'
    )
    # Parse known args to separate --src_dst from the rest
    known_args, extra_args = parser.parse_known_args()

    logger.info(f"Parsed src_dst pairs: {known_args.src_dst}")
    logger.info(f"Extra rsync args: {extra_args}")
    if not known_args.src_dst:
        logger.error('No --src_dst argument provided.')
        raise ValueError('At least one --src_dst argument is required.')
    for pair in known_args.src_dst:
        if len(pair) != 2:
            logger.error(f'Invalid --src_dst pair: {pair}')
            raise ValueError('Each --src_dst argument must contain exactly two paths separated by a comma.')
    return known_args, extra_args


async def run_rsync(src, dst, idx=0, extra_args=None):
    cmd = ["rsync"]
    if extra_args:
        cmd.extend(extra_args)
    cmd.extend([src, dst])
    logger.info(f"Starting rsync: {' '.join(cmd)}")
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    prefix = f"[src{idx+1}] "
    if process.stdout is not None:
        print(f'{prefix}', end="")
        while True:
            b = await process.stdout.read(1)
            if not b:
                break
            print(f'{b.decode().replace('\n', f'\n{prefix}')}', end='')
            logger.debug(f"{prefix}{b.decode().strip()}")
    retcode = await process.wait()
    logger.info(f"Rsync for {src} -> {dst} exited with code {retcode}")


async def main():
    setup_logger()
    args, extra_args = parse_args()
    src_dst_pairs = args.src_dst
    logger.info(f"Launching {len(src_dst_pairs)} rsync jobs in parallel.")
    coros = [run_rsync(src, dst, idx=idx, extra_args=extra_args) for idx, (src, dst) in enumerate(src_dst_pairs)]
    await asyncio.gather(*coros)
    logger.info("All rsync jobs completed.")


if __name__ == "__main__":
    asyncio.run(main())
