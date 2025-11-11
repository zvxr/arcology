import asyncio
import argparse
from bridge import unified_search

def main():
    parser = argparse.ArgumentParser(prog="mcp-bridge", description="CLI bridge for MCP/Obsidian")
    sub = parser.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("query", help="Search for a term")
    q.add_argument("term", help="Search string, e.g. 'boros'")
    q.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.cmd == "query":
        results = asyncio.run(unified_search(args.term))
        print(f"### Results for `{args.term}` (showing up to {args.limit})\n")
        for i, r in enumerate(results[: args.limit], 1):
            path = r.get("path") or r.get("id") or "unknown"
            snippet = (r.get("snippet") or "").strip().replace("\n", " ")
            score = r.get("score")
            score_s = f" _(score {score})_" if score is not None else ""
            print(f"{i}. **{path}**{score_s}\n    - {snippet[:220]}\n")

if __name__ == "__main__":
    main()