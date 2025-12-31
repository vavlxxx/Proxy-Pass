import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.caching_proxy.cache import cache
from src.caching_proxy.config import settings
from src.caching_proxy.server import run_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI for Caching Proxy Server",
        epilog="Run `caching-proxy --help` for more information",
    )
    subparsers = parser.add_subparsers(
        required=True,
        dest="command",
    )
    parser_run = subparsers.add_parser(
        "run",
        help="Run the caching proxy server",
    )
    parser_clear = subparsers.add_parser(
        "clear",
        help="Clear the cache",
    )
    parser_run.add_argument(
        "-p",
        "--port",
        type=int,
        default=settings.CACHE_DEFAULT_PORT,
        help="Port on which the server will run. Default value is %s" % settings.CACHE_DEFAULT_PORT,
    )
    parser_run.add_argument(
        "-o",
        "--origin",
        type=str,
        required=True,
        help="Origin server URL from which requests will be proxied",
    )
    parser_run.add_argument(
        "--ttl",
        type=int,
        default=settings.CACHE_DEFAULT_TTL,
        help="TTL for cache entries. Zero means no TTL. Negative values automatically set the TTL to 0. Default value is %s"
        % settings.CACHE_DEFAULT_TTL,
    )
    parser_run.set_defaults(func=run_proxy)
    parser_clear.set_defaults(func=clear_cache)
    return parser


def run_proxy(args):
    run_server(args)


def clear_cache(args):
    cache.clear()
    print("Cache is now empty...")


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
