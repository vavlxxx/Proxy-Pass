import argparse
import subprocess
import sys
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.caching_proxy.config import settings
from src.caching_proxy.schemas import AppConfig, AppStatus
from src.caching_proxy.server import run_server
from src.caching_proxy.utils import ConfigHelper


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
    parser_stop = subparsers.add_parser(
        "stop",
        help="Stop the proxy server",
    )
    parser_keys = subparsers.add_parser(
        "keys",
        help="Displays all keys stored in the cache",
    )
    parser_health = subparsers.add_parser(
        "health",
        help="Displays basic info about running proxy server",
    )
    parser_health.add_argument(
        "-p",
        "--port",
        type=int,
        required=False,
        help="Port on which the server runnning. If port is not specified, displays all running servers",
    )
    parser_run.add_argument(
        "-d",
        "--detached",
        action="store_true",
        help="Run the server in detached mode",
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
    parser_keys.set_defaults(func=show_keys)
    parser_health.set_defaults(func=status_proxy)
    parser_stop.set_defaults(func=stop_proxy)
    parser_run.set_defaults(func=run_proxy)
    parser_clear.set_defaults(func=clear_cache)
    return parser


def run_proxy(args):
    if args.detached:
        log = open(settings.LOG_FILE, "a", buffering=1, encoding="utf-8")

        cmd = [
            sys.executable,
            "-m",
            "src.caching_proxy.cli",
            "run",
            "-o",
            args.origin,
            "-p",
            str(args.port),
            "--ttl",
            str(args.ttl),
        ]

        if sys.platform == "win32":
            subprocess.Popen(
                cmd,
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            )
        else:
            subprocess.Popen(
                cmd,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )

        print(f"Started Proxy Server in DETACHED mode on http://{settings.CACHE_DEFAULT_HOST}:{args.port}")
        return

    config = AppConfig(host=settings.CACHE_DEFAULT_HOST, port=args.port)
    ConfigHelper.write_config(config=config)
    run_server(args)


def status_proxy(args):
    config: AppConfig = ConfigHelper.read_config()
    url = f"http://{config.host}:{config.port}/{settings.ADMIN_API_PREFIX}/__health"
    resp = httpx.get(url, headers=settings.HTTPX_HEADERS)
    data = resp.json()
    status = AppStatus.model_validate(data)
    print("Proxy Server is running:")
    print(f"HOST: http://{status.host}:{status.port}")
    print(f"ORIGIN: {status.origin}")
    print(f"Cache TTL: {status.ttl}")


def stop_proxy(args):
    config: AppConfig = ConfigHelper.read_config()
    url = f"http://{config.host}:{config.port}/{settings.ADMIN_API_PREFIX}/__shutdown"
    _ = httpx.post(url, headers=settings.HTTPX_HEADERS)
    print("Proxy Server has been stopped...")


def clear_cache(args):
    config: AppConfig = ConfigHelper.read_config()
    url = f"http://{config.host}:{config.port}/{settings.ADMIN_API_PREFIX}/__clear"
    _ = httpx.post(url, headers=settings.HTTPX_HEADERS)
    print("Proxy Server cache has been cleared")


def show_keys(args):
    config: AppConfig = ConfigHelper.read_config()
    url = f"http://{config.host}:{config.port}/{settings.ADMIN_API_PREFIX}/__keys"
    resp = httpx.post(url, headers=settings.HTTPX_HEADERS)
    if resp.is_success:
        keys = resp.json().get("keys", [])
        if not keys:
            print("Cache is empty")
            return

        for i, key in enumerate(start=1, iterable=keys):
            print(f"{i}) '{key}'")


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
