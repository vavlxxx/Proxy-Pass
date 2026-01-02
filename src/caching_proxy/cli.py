import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.caching_proxy.client import client
from src.caching_proxy.config import settings
from src.caching_proxy.schemas import AppConfig, AppStatus
from src.caching_proxy.server import run_server
from src.caching_proxy.utils import CachingHelper, cfg


def show_server_info(server: AppStatus, prefix: str = "") -> None:
    if prefix:
        print(prefix)

    host = CachingHelper.join_host_and_port(settings.HOST, server.port)
    print(f"Host:   {host}")
    print(f"Origin: {server.origin}")
    print(f"TTL:    {server.ttl}s")


def get_server_on_port(port: int) -> AppStatus | None:
    status = client.get_status(port)
    if status is None:
        host = CachingHelper.join_host_and_port(settings.HOST, port)
        print(f"No server running on {host}")
    return status


def run_proxy_detached(args):
    log = open(settings.LOG_FILE, "a", buffering=1, encoding="utf-8")
    module_path = "src.caching_proxy.cli"
    cmd = [
        sys.executable,
        "-m",
        module_path,
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
        subprocess.Popen(cmd, stdout=log, stderr=log, start_new_session=True)

    host = CachingHelper.join_host_and_port(settings.HOST, args.port)
    print(f"Started proxy server in DETACHED mode on {host}")


def run_proxy(args):
    status = get_server_on_port(args.port)
    if status is not None:
        show_server_info(status, prefix="Proxy server is already running:")
        return
    if args.detached:
        run_proxy_detached(args)
        return

    run_server(args)


def status_proxy(args):
    if hasattr(args, "port") and args.port:
        status = get_server_on_port(port=args.port)
        if status is None:
            return

        show_server_info(status, prefix="Proxy server is running:")
        return

    config: AppConfig = cfg.read_config()
    servers = config.servers
    if not servers:
        print("No proxy servers are running!")
        return

    for i, server in enumerate(iterable=servers, start=1):
        status = client.get_status(server.port)
        if status:
            show_server_info(status, prefix=f"\nproxy server {i} is running")


def stop_proxy(args):
    status = get_server_on_port(port=args.port)
    if status is None:
        return

    host = CachingHelper.join_host_and_port(settings.HOST, args.port)
    if client.shutdown(args.port):
        print(f"Server on {host} has been stopped")
        cfg.remove_server_from_config(args.port)
        return

    print(f"Failed to stop server on {host}")


def clear_cache(args):
    status = get_server_on_port(port=args.port)
    if status is None:
        return

    host = CachingHelper.join_host_and_port(settings.HOST, args.port)
    if client.clear_cache(args.port):
        host = CachingHelper.join_host_and_port(settings.HOST, args.port)
        print(f"Sussessfully cleared cache on {host}")
        return

    print(f"Failed to clear cache on {host}")


def show_keys(args):
    status = get_server_on_port(args.port)
    if not status:
        return

    keys = client.get_keys(args.port)
    if not keys:
        print("Cache is empty")
        return

    print(f"Cache keys ({len(keys)}):")
    current_time = time.time()
    for i, key in enumerate(keys, 1):
        expires = "N/A"
        if key[1] is not None:
            expires = str(key[1] - current_time)

        print(f"{i:>3}. {key[0]: <50} EXPIRES IN: {expires} sec")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="caching-proxy",
        description="CLI for caching proxy server",
        epilog="Run `caching-proxy --help` for more information",
    )
    subparsers = parser.add_subparsers(required=True, dest="command")
    port_arg = {"flags": ["-p", "--port"], "type": int, "help": "Server port"}

    parser_run = subparsers.add_parser("run", help="Run the caching proxy server")
    parser_run.add_argument(*port_arg["flags"], **{k: v for k, v in port_arg.items() if k != "flags"}, required=True)
    parser_run.add_argument("-d", "--detached", action="store_true", help="Run the server in detached mode")
    parser_run.add_argument("-o", "--origin", type=str, required=True, help="Origin server URL")
    parser_run.add_argument("--ttl", type=int, default=settings.TTL, help=f"TTL in seconds, default: {settings.TTL}")
    parser_run.set_defaults(func=run_proxy)

    parser_clear = subparsers.add_parser("clear", help="Cleans the cache")
    parser_clear.add_argument(*port_arg["flags"], **{k: v for k, v in port_arg.items() if k != "flags"}, required=True)
    parser_clear.set_defaults(func=clear_cache)

    parser_stop = subparsers.add_parser("stop", help="Stop the proxy server")
    parser_stop.add_argument(*port_arg["flags"], **{k: v for k, v in port_arg.items() if k != "flags"}, required=True)
    parser_stop.set_defaults(func=stop_proxy)

    parser_keys = subparsers.add_parser("keys", help="Displays all keys stored in the cache")
    parser_keys.add_argument(*port_arg["flags"], **{k: v for k, v in port_arg.items() if k != "flags"}, required=True)
    parser_keys.set_defaults(func=show_keys)

    parser_health = subparsers.add_parser("health", help="Displays basic info about running proxy server")
    parser_health.add_argument(*port_arg["flags"], **{k: v for k, v in port_arg.items() if k != "flags"}, required=False)
    parser_health.set_defaults(func=status_proxy)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
