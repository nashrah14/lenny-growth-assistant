"""
Command-Line Interface (CLI) for The Lenny Growth Assistant
Provides commands for dataset ingestion, health checks, and database migrations.
"""
import sys
import argparse
import asyncio

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from rich.console import Console
from rich.table import Table
from backend.app.core.logging import setup_logging
from backend.app.rag.ingestion import IngestionPipeline
from backend.app.db.session import init_db
from backend.app.rag.qdrant import qdrant_adapter
from backend.app.llm.router import llm_router

console = Console(force_terminal=True, legacy_windows=False)

async def run_ingest(args):
    console.print(f"[bold cyan]⚡ Running Transcript Ingestion Pipeline[/bold cyan]")
    if args.dry_run:
        console.print("[yellow]Mode: Dry Run (No vectors will be saved)[/yellow]")
    if args.limit:
        console.print(f"[yellow]Processing Limit: {args.limit} transcripts[/yellow]")

    pipeline = IngestionPipeline()
    result = await pipeline.run(
        limit=args.limit,
        dry_run=args.dry_run,
        rebuild=args.rebuild
    )

    table = Table(title="Ingestion Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for k, v in result.items():
        table.add_row(str(k), str(v))

    console.print(table)


async def run_health(args):
    console.print("[bold cyan]🔍 Checking System Health & Connectivity[/bold cyan]")
    
    # 1. Database
    try:
        await init_db()
        console.print("  [green]✓ PostgreSQL / Database: Connected & Schema Initialized[/green]")
    except Exception as e:
        console.print(f"  [red]✗ Database: Failed ({e})[/red]")

    # 2. Qdrant
    q_health = await qdrant_adapter.health()
    if q_health.get("status") == "healthy":
        console.print(f"  [green]✓ Qdrant Cloud: Connected (Points: {q_health.get('points_count', 0)})[/green]")
    else:
        console.print(f"  [yellow]⚠ Qdrant Cloud: {q_health.get('status')} ({q_health.get('error', 'Degraded')})[/yellow]")

    # 3. LLMs
    llm_health = await llm_router.get_health_status()
    for provider, is_healthy in llm_health.items():
        if is_healthy:
            console.print(f"  [green]✓ LLM Provider '{provider}': Available[/green]")
        else:
            console.print(f"  [yellow]⚠ LLM Provider '{provider}': Unreachable / Key missing[/yellow]")


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="The Lenny Growth Assistant CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest podcast transcripts into vector store & BM25")
    ingest_parser.add_argument("--limit", type=int, default=None, help="Limit number of transcripts to ingest")
    ingest_parser.add_argument("--dry-run", action="store_true", help="Perform parsing and chunking without indexing")
    ingest_parser.add_argument("--rebuild", action="store_true", help="Force rebuild existing indices")

    # Health command
    subparsers.add_parser("health", help="Check database, Qdrant, and LLM connectivity")

    # Init DB command
    subparsers.add_parser("init-db", help="Initialize database tables")

    args = parser.parse_args()

    if args.command == "ingest":
        asyncio.run(run_ingest(args))
    elif args.command == "health":
        asyncio.run(run_health(args))
    elif args.command == "init-db":
        asyncio.run(init_db())
        console.print("[green]Database initialized successfully![/green]")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
