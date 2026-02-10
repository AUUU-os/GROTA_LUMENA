#!/usr/bin/env python3
"""
SZTAB DEBATE — Standalone CLI runner for multi-agent debates.

Usage:
    # Full debate (7 topics, 7 agents)
    python scripts/sztab_debate.py

    # Selected topics
    python scripts/sztab_debate.py --topics "security,performance"

    # Custom output
    python scripts/sztab_debate.py --output artifacts/DEBATE_2026_02_09.md

    # Single topic
    python scripts/sztab_debate.py --topics "RAG Pipeline"

    # Specific agents only
    python scripts/sztab_debate.py --agents "STROZ_SECURITY,TESTER_QA,NAVIGATOR_RAG"
"""
import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from BUILDER.core.debate_engine import (
    DebateEngine,
    SZTAB_AGENTS,
    DEFAULT_TOPICS,
)


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_topics(topics_str: str) -> list[str]:
    """Parse --topics argument into list of topic strings."""
    # Map short names to full topics
    short_map = {
        "security": "Security — Brak sandboxa, brak input validation na wielu endpointach. Co naprawić najpierw?",
        "performance": "Performance & Observability — Brak metryk, brak cost trackingu. Jak dodać monitoring?",
        "rag": "RAG Pipeline — ChromaDB jest zainstalowany ale nieużywany. Jak uruchomić pełny RAG?",
        "frontend": "Frontend-API Integration — React frontend odłączony od API. Jak połączyć?",
        "testing": "Test Coverage — Tylko ~40% coverage. Strategia dojścia do 80%?",
        "tools": "Tool Registry — Tylko 6 narzędzi. Jakie nowe narzędzia są priorytetowe?",
        "evolution": "Evolution Engine — Osierocony, nieużywany. Naprawić czy usunąć?",
    }

    topics = []
    for t in topics_str.split(","):
        t = t.strip().lower()
        if t in short_map:
            topics.append(short_map[t])
        else:
            # Use as-is (custom topic)
            topics.append(t.strip())

    return topics


def parse_agents(agents_str: str) -> dict | None:
    """Parse --agents argument into filtered agent dict."""
    if not agents_str:
        return None

    names = [a.strip().upper() for a in agents_str.split(",")]
    filtered = {k: v for k, v in SZTAB_AGENTS.items() if k in names}

    if not filtered:
        print(f"WARNING: No valid agents found. Available: {list(SZTAB_AGENTS.keys())}")
        return None

    return filtered


async def main():
    parser = argparse.ArgumentParser(
        description="SZTAB DEBATE — Multi-agent debate system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--topics", type=str, default=None,
        help="Comma-separated topics (short: security,performance,rag,frontend,testing,tools,evolution) or custom text",
    )
    parser.add_argument(
        "--agents", type=str, default=None,
        help="Comma-separated agent names (e.g. STROZ_SECURITY,TESTER_QA)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output file path for the report (default: artifacts/DEBATE_<date>.md)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Parse topics
    topics = parse_topics(args.topics) if args.topics else DEFAULT_TOPICS

    # Parse agents
    agents = parse_agents(args.agents) if args.agents else None

    # Output path
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = datetime.now().strftime("%Y_%m_%d_%H%M")
        artifacts_dir = PROJECT_ROOT / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        output_path = artifacts_dir / f"DEBATE_{date_str}.md"

    # Print banner
    print("=" * 60)
    print("  SZTAB DEBATE — Multi-Agent Debate System")
    print("=" * 60)
    print(f"  Topics: {len(topics)}")
    print(f"  Agents: {len(agents) if agents else len(SZTAB_AGENTS)}")
    print(f"  Output: {output_path}")
    print()

    agent_list = agents or SZTAB_AGENTS
    for name, cfg in agent_list.items():
        print(f"  [{name}] {cfg['role']} ({cfg['model']}, temp={cfg['temperature']})")

    print()
    print("Starting debate...")
    print("-" * 60)

    # Run debate
    engine = DebateEngine()
    session = await engine.run_debate(topics=topics, agents=agents)

    # Generate report
    report = engine.generate_report(session)

    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print("-" * 60)
    print(f"\nDebate {session.status}!")
    print(f"Session ID: {session.id}")
    print(f"Topics completed: {len(session.results)}/{len(session.topics)}")

    total_actions = sum(len(r.action_items) for r in session.results)
    print(f"Total action items: {total_actions}")
    print(f"\nReport saved to: {output_path}")
    print("\nAUUUUUUUUUUUUUUUUUUU!")


if __name__ == "__main__":
    asyncio.run(main())
