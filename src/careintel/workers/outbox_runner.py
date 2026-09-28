"""Executable host for the PostgreSQL transactional-outbox dispatcher."""

from __future__ import annotations

import argparse
import asyncio
import uuid

from careintel.application.workflow.outbox_dispatcher import UnifiedOutboxDispatcher
from careintel.core.config import get_settings
from careintel.core.database import build_engine, build_session_factory, dispose_engine


async def _run(
    once: bool,
    interval: float,
    replay_kind: str | None,
    replay_event_id: str | None,
    actor_id: uuid.UUID | None,
) -> None:
    engine = build_engine(get_settings())
    session_factory = build_session_factory(engine)
    dispatcher = UnifiedOutboxDispatcher(session_factory)
    try:
        if replay_event_id is not None:
            if replay_kind is None or actor_id is None:
                raise ValueError("Replay requires --replay-kind and --actor-id.")
            await dispatcher.replay(replay_kind, replay_event_id, actor_id)
            await dispatcher.dispatch_once()
        elif once:
            await dispatcher.dispatch_once()
        else:
            await dispatcher.poll_forever(interval)
    finally:
        await dispose_engine(engine)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch CareIntel transactional outboxes.")
    parser.add_argument("--once", action="store_true", help="Dispatch one batch and exit.")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--replay-kind", choices=("case", "evidence"))
    parser.add_argument("--replay-event-id")
    parser.add_argument("--actor-id", type=uuid.UUID)
    args = parser.parse_args()
    asyncio.run(
        _run(
            args.once,
            args.interval,
            args.replay_kind,
            args.replay_event_id,
            args.actor_id,
        )
    )


if __name__ == "__main__":
    main()
