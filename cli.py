#!/usr/bin/env python3
"""GeoRecon CLI entry point."""

import argparse
import json
import logging
from pathlib import Path
import sys

from colorama import Fore
import pyfiglet
import uvicorn
import yaml

from server.tg_sync import tgBot


def print_banner():
    font = "slant"
    ascii_banner = pyfiglet.figlet_format("GeoRecon", font=font)
    print(Fore.RED + ascii_banner)
    print(Fore.GREEN)
    print("Welcome you here!\n")


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


def load_registry() -> dict:
    p = Path("templates/meta.json")
    if not p.exists():
        print("[!] templates/meta.json not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(p.read_text(encoding="utf-8"))


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
    fmt = "%(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=fmt,
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stderr)],
        force=True,
    )
    # Suppress ALL uvicorn and third-party logs
    for name in (
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "uvicorn.asgi",
        "watchfiles",
        "httpx",
    ):
        logging.getLogger(name).setLevel(logging.CRITICAL)


def merge_config(cli_args: argparse.Namespace) -> dict:
    """Merge CLI args with YAML config. CLI has priority."""
    yaml_cfg = load_config(cli_args.config)
    return {
        "host": cli_args.host
        if cli_args.host != "0.0.0.0"
        else yaml_cfg.get("host", "0.0.0.0"),
        "port": cli_args.port if cli_args.port != 8000 else yaml_cfg.get("port", 8000),
        "log_level": cli_args.log_level
        if cli_args.log_level != "info"
        else yaml_cfg.get("log_level", "info"),
        "no_access_log": cli_args.no_access_log or yaml_cfg.get("no_access_log", False),
    }


def main() -> None:
    try:
        args = parse_args()
        setup_logging(args.log_level)
        print_banner()

        config = merge_config(args)

        registry = load_registry()
        templates = registry.get("templates", [])
        if not templates:
            logging.error("No templates found")
            sys.exit(1)

        logging.info("Select template:")
        for i, t in enumerate(templates):
            logging.info(f"  [{i}] {t['name']}")

        try:
            idx = int(input("[>] "))
            if not (0 <= idx < len(templates)):
                raise ValueError
        except (ValueError, IndexError):
            logging.error("Invalid input")
            sys.exit(1)

        selected = templates[idx]
        dir_name = selected["dir_name"]
        defaults = selected.get("defaults", {}).copy()

        logging.info(f"Configuring '{selected['name']}':")
        context = {}
        for key, default_val in defaults.items():
            prompt = f"  • {key} [by default: {default_val}]: "
            val = input(prompt).strip()
            context[key] = val if val else default_val

        use_tg = input("\nDo you want to duplicate msgs to Telegram? [y/n] -> ")
        if use_tg == "y":
            tgBot.setup_interactive()
        else:
            logging.info("Ok, process without Telegram")

        try:
            from server.main import app as geo_app

            geo_app.state.template_dir = f"templates/{dir_name}"
            geo_app.state.context = context
            tgBot.configure_app_state(geo_app)

        except ImportError as e:
            logging.error(f"Failed to import application: {e}")
            sys.exit(1)

        uvicorn_kwargs = {
            "app": geo_app,
            "host": config["host"],
            "port": config["port"],
            "log_level": "error",
            "log_config": None,
            "use_colors": False,
            "access_log": not config["no_access_log"],
        }

        logging.info(f"Listening on http://{config['host']}:{config['port']}")

        try:
            uvicorn.run(**uvicorn_kwargs)
        except KeyboardInterrupt:
            logging.info("\nInterrupted by user")
        except Exception:
            logging.error("\nServer stopped unexpectedly")
        finally:
            logging.info("\nServer has been shut down gracefully. Bye!")
    except KeyboardInterrupt:
        logging.info("\nShutdown requested, bye...")
    except Exception:
        logging.critical("Server error")


if __name__ == "__main__":
    main()
