from __future__ import annotations

import argparse
import asyncio
import logging
import threading

import uvicorn

from anderbot.bot import AnderBot
from anderbot.config import settings
from anderbot.web.app import create_app


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def run_bot() -> None:
    bot = AnderBot()
    app = create_app(bot)

    config = uvicorn.Config(app, host=settings.anderbot_host, port=settings.anderbot_port, log_level="info")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    await bot.serve_forever()


def cli() -> None:
    parser = argparse.ArgumentParser(description="AnderBot")
    parser.add_argument("command", nargs="?", default="run", choices=["run"])
    parser.parse_args()
    setup_logging()
    asyncio.run(run_bot())


if __name__ == "__main__":
    cli()
