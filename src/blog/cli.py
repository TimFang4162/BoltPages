"""Command line interface."""

import argparse
from pathlib import Path

from blog.builder import Builder
from blog.config import Config
from blog.devserver import DevServer, serve_static
from blog.utils import console


def build_command(args: argparse.Namespace) -> None:
    """Handle build command.
    
    Args:
        args: Parsed command line arguments
    """
    config = Config.load(args.config)
    
    if args.no_cache:
        config.build.cache = False
    
    builder = Builder(config)
    builder.build()


def dev_command(args: argparse.Namespace) -> None:
    """Handle dev command.
    
    Args:
        args: Parsed command line arguments
    """
    config = Config.load(args.config)
    
    if args.port:
        config.dev.port = args.port
    if args.host:
        config.dev.host = args.host
    if args.debounce is not None:
        config.dev.debounce = args.debounce
    
    console.log("[cyan]Running initial build...[/cyan]")
    builder = Builder(config)
    builder.build()
    
    server = DevServer(config)
    server.serve()


def server_command(args: argparse.Namespace) -> None:
    """Handle server command.
    
    Args:
        args: Parsed command line arguments
    """
    config = Config.load(args.config)
    
    if args.port:
        config.dev.port = args.port
    if args.host:
        config.dev.host = args.host
    
    serve_static(config)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="blog",
        description="Modern static blog generator with markdown, typst support and dev server"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    build_parser = subparsers.add_parser("build", help="Build the site")
    build_parser.add_argument(
        "--no-cache", action="store_true",
        help="Disable caching and rebuild all files"
    )
    build_parser.add_argument(
        "--config", default="config.toml",
        help="Path to configuration file (default: config.toml)"
    )
    
    dev_parser = subparsers.add_parser("dev", help="Start development server with live reload")
    dev_parser.add_argument(
        "--port", type=int,
        help="Port to serve on (default: from config)"
    )
    dev_parser.add_argument(
        "--host",
        help="Host to bind to (default: from config)"
    )
    dev_parser.add_argument(
        "--debounce", type=float,
        help="Debounce delay in seconds (default: from config)"
    )
    dev_parser.add_argument(
        "--config", default="config.toml",
        help="Path to configuration file (default: config.toml)"
    )
    
    server_parser = subparsers.add_parser("server", help="Serve static files without live reload")
    server_parser.add_argument(
        "--port", type=int,
        help="Port to serve on (default: from config)"
    )
    server_parser.add_argument(
        "--host",
        help="Host to bind to (default: from config)"
    )
    server_parser.add_argument(
        "--config", default="config.toml",
        help="Path to configuration file (default: config.toml)"
    )
    
    args = parser.parse_args()
    
    if args.command == "build":
        build_command(args)
    elif args.command == "dev":
        dev_command(args)
    elif args.command == "server":
        server_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
