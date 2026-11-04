"""Command line: ``ashariri ingest | serve | chat | eval``."""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid

from .config import get_settings
from .service import Service


def _ingest(args: argparse.Namespace) -> None:
    count = Service.from_settings(get_settings()).ingest()
    print(f"Indexed {count} passages.")


def _serve(args: argparse.Namespace) -> None:
    import uvicorn

    uvicorn.run("ashariri.api:create_app", factory=True, host=args.host, port=args.port, reload=args.reload)


def _chat(args: argparse.Namespace) -> None:
    service = Service.from_settings(get_settings())
    service.ensure_ingested()
    session, history = uuid.uuid4().hex, []
    print("Ask Balaji's twin anything. Ctrl-D to quit.\n")

    async def turn(question: str) -> str:
        answer = ""
        async for event in service.ask(question, session, history):
            kind = event["type"]
            if kind == "token":
                print(event["text"], end="", flush=True)
            elif kind == "reset":
                print("\n  ~ revising ~\n", end="", flush=True)
            elif kind == "replace":
                print(event["text"], end="", flush=True)
            elif kind == "step" and args.trace and event["status"] != "running":
                print(f"  · {event['node']}: {event.get('detail', event['status'])}", file=sys.stderr)
            elif kind == "final":
                answer = event["answer"]
        print("\n")
        return answer

    while True:
        try:
            question = input("you › ").strip()
        except EOFError:
            print()
            return
        if question:
            answer = asyncio.run(turn(question))
            history += [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]


def _eval(args: argparse.Namespace) -> None:
    from .evals import run

    sys.exit(0 if asyncio.run(run(args.cases, verbose=args.verbose)) else 1)


def main() -> None:
    parser = argparse.ArgumentParser(prog="ashariri", description="Balaji's digital twin.")
    commands = parser.add_subparsers(required=True)

    commands.add_parser("ingest", help="index the knowledge folder").set_defaults(run=_ingest)

    serve = commands.add_parser("serve", help="run the HTTP API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")
    serve.set_defaults(run=_serve)

    chat = commands.add_parser("chat", help="chat in the terminal")
    chat.add_argument("--trace", action="store_true", help="print each graph step")
    chat.set_defaults(run=_chat)

    evals = commands.add_parser("eval", help="run the evaluation suite")
    evals.add_argument("--cases", default=None, help="path to a cases YAML file")
    evals.add_argument("--verbose", action="store_true")
    evals.set_defaults(run=_eval)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
