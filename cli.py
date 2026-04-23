#!/usr/bin/env python3
"""GeoRecon CLI entry point."""

import argparse
import logging
import sys
from pathlib import Path

import pyfiglet
import yaml
import uvicorn
from colorama import Fore


def print_banner():
    font = "slant"
    ascii_banner = pyfiglet.figlet_format("GeoRecon", font=font)
    print(Fore.GREEN + ascii_banner)


def load_config(path: str) -> dict:
    """Load YAML config file. Return empty dict if not found."""
    config_path = Path(path)
    if not config_path.exists():
        return {}
    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="GeoRecon",
        description="Asynchronous geolocation capture service",
        add_help=True,
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    parser.add_argument("--config", default="geoconf.yaml", help="Path to YAML config")
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--no-access-log",
        action="store_true",
        help="Disable uvicorn access log",
    )
    parser.add_argument("-v", "--version", action="version", version="GeoRecon 1.0.0")
    return parser.parse_args()


def setup_logging(level: str) -> None:
    """Configure logging: only GeoRecon logs to stderr."""
    fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=fmt,
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stderr)],
        force=True,
    )
    # Suppress ALL uvicorn and third-party logs
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "uvicorn.asgi", "watchfiles"):
        logging.getLogger(name).setLevel(logging.CRITICAL)


def merge_config(cli_args: argparse.Namespace) -> dict:
    """Merge CLI args with YAML config. CLI has priority."""
    yaml_cfg = load_config(cli_args.config)
    return {
        "host": cli_args.host if cli_args.host != "0.0.0.0" else yaml_cfg.get("host", "0.0.0.0"),
        "port": cli_args.port if cli_args.port != 8000 else yaml_cfg.get("port", 8000),
        "log_level": cli_args.log_level if cli_args.log_level != "info" else yaml_cfg.get("log_level", "info"),
        "no_access_log": cli_args.no_access_log or yaml_cfg.get("no_access_log", False),
    }


def main() -> None:
    args = parse_args()
    setup_logging(args.log_level)
    print_banner()

    config = merge_config(args)

    try:
        from server.main import app as geo_app
    except ImportError as e:
        logging.error(f"Failed to import application: {e}")
        sys.exit(1)

    uvicorn_kwargs = {
        "app": geo_app,
        "host": config["host"],
        "port": config["port"],
        "log_level": "error",  # Only real errors from uvicorn
        "log_config": None,
        "use_colors": False,
        "access_log": not config["no_access_log"],
    }

    logging.info(f"Listening on http://{config['host']}:{config['port']}")

    try:
        uvicorn.run(**uvicorn_kwargs)
    except KeyboardInterrupt:
        logging.info("Shutdown requested")
    except Exception as e:
        logging.critical(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()