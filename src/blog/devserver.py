"""Development server with file watching and live reload."""

import logging
import os
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from livereload import Server
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from blog.builder import Builder
from blog.config import Config
from blog.utils import console

logger = logging.getLogger("rich")


class FileChangeHandler(FileSystemEventHandler):
    """Handle file system change events."""
    
    def __init__(self, callback: "DevServer", build_dir: str) -> None:
        """Initialize handler.
        
        Args:
            callback: DevServer instance
            build_dir: Build directory to ignore
        """
        self.callback = callback
        self.build_dir = Path(build_dir).resolve()
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
    
    def on_modified(self, event) -> None:
        """Handle file modification event."""
        if event.is_directory:
            return
        
        src_path = event.src_path if isinstance(event.src_path, str) else event.src_path.decode()
        file_path = Path(src_path).resolve()
        
        # Skip if the file is in the build directory
        try:
            file_path.relative_to(self.build_dir)
            return
        except ValueError:
            pass
        
        # Only process specific file types
        if file_path.suffix not in {".md", ".html", ".css", ".js", ".toml"}:
            return
        
        console.log(f"[yellow]Change detected:[/yellow] {file_path}")
        
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            
            self._timer = threading.Timer(0.5, self.callback.trigger_rebuild)
            self._timer.start()


class DevServer:
    """Development server with file watching and live reload."""
    
    def __init__(self, config: Config) -> None:
        """Initialize dev server.
        
        Args:
            config: Blog configuration
        """
        self.config = config
        self.builder = Builder(config)
        self.observer = Observer()
        self._livereload_server: Server | None = None
        self._is_rebuilding = False
        self._reload_trigger_file = Path(config.build.output_dir) / ".reload_trigger"
    
    def serve(self) -> None:
        """Start development server."""
        console.log(f"[blue]Starting dev server at http://{self.config.dev.host}:{self.config.dev.port}[/blue]")
        
        Path(self.config.build.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create trigger file for livereload
        self._reload_trigger_file.touch()
        
        self._start_livereload()
        self._start_file_watcher()
    
    def _start_livereload(self) -> None:
        """Start livereload server in a separate thread."""
        server = Server()
        self._livereload_server = server
        
        original_dir = os.getcwd()
        os.chdir(self.config.build.output_dir)
        
        try:
            # Watch the trigger file for livereload
            # When we modify this file, livereload will reload the browser
            server.watch(
                str(self._reload_trigger_file.name),
                func=None,  # No callback, just trigger reload
                delay=None
            )
            
            server_thread = threading.Thread(
                target=self._run_livereload,
                args=(server, original_dir),
                daemon=True
            )
            server_thread.start()
            time.sleep(1)
        finally:
            os.chdir(original_dir)
    
    def _run_livereload(self, server: Server, original_dir: str) -> None:
        """Run the livereload server."""
        try:
            server.serve(
                host=self.config.dev.host,
                port=self.config.dev.port,
                live_css=False,
                open_url_delay=None,
                root=os.getcwd(),
            )
        finally:
            os.chdir(original_dir)
    
    def _start_file_watcher(self) -> None:
        """Start file system watcher."""
        handler = FileChangeHandler(callback=self, build_dir=self.config.build.output_dir)
        
        for watch_dir in self.config.dev.watch_dirs:
            watch_path = Path(watch_dir)
            if watch_path.exists():
                self.observer.schedule(handler, str(watch_path), recursive=True)
                console.log(f"[dim]Watching: {watch_path}[/dim]")
        
        self.observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        
        self.observer.join()
    
    def trigger_rebuild(self) -> None:
        """Trigger rebuild with debounce protection."""
        if self._is_rebuilding:
            console.log("[dim]Skipping rebuild (already rebuilding)[/dim]")
            return
        
        self._is_rebuilding = True
        
        console.log("[cyan]Rebuilding...[/cyan]")
        try:
            self.builder.build()
            console.log("[green]Build complete![/green]")
            
            # Trigger livereload by modifying the trigger file
            self._trigger_browser_reload()
        except Exception as e:
            console.log(f"[red]Build failed: {e}[/red]")
            logger.exception("Build failed")
        finally:
            time.sleep(1.0)
            self._is_rebuilding = False
    
    def _trigger_browser_reload(self) -> None:
        """Trigger browser reload by touching the watched file."""
        try:
            # Update the trigger file's modification time
            self._reload_trigger_file.touch()
            console.log("[dim]Browser reload triggered[/dim]")
        except Exception as e:
            logger.warning(f"Failed to trigger browser reload: {e}")


def serve_static(config: Config) -> None:
    """Serve static files without live reload.
    
    Args:
        config: Blog configuration
    """
    console.log(f"[blue]Starting server at http://{config.dev.host}:{config.dev.port}[/blue]")
    console.log("[dim]Press Ctrl+C to stop[/dim]")
    
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=config.build.output_dir, **kwargs)
        
        def log_message(self, format, *args):
            pass
    
    server = HTTPServer((config.dev.host, config.dev.port), Handler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.log("\n[yellow]Server stopped[/yellow]")
        server.shutdown()
