"""Main build orchestrator."""

import hashlib
import logging
from pathlib import Path

from blog.assets import build_static
from blog.builders import build_archive, build_errors, build_index, build_posts, build_tags, build_tags_index
from blog.cache import read_lock, restore_metadata_from_cache
from blog.config import Config
from blog.models import Post
from blog.utils import setup_logging

logger = logging.getLogger("rich")


class Builder:
    """Main builder orchestrator."""
    
    def __init__(self, config: Config) -> None:
        """Initialize builder.
        
        Args:
            config: Blog configuration
        """
        self.config = config
        self.logger = setup_logging(config.build.log_level)
        self.posts: list[Post] = []
        from typing import Any
        self.lock: dict[str, dict[str, Any]] = {}
        self.asset_hashes: dict[str, str] = {}
    
    def build(self) -> None:
        """Run full build process."""
        self.logger.info(f"Building {self.config.site.name}...")
        
        Path(self.config.build.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Clear posts list before each build to prevent accumulation
        self.posts.clear()
        
        self.lock = read_lock(self.config.build.cache)
        self._find_markdown_files()
        restore_metadata_from_cache(self.posts, self.lock, self.config.build.cache)
        
        # Build static files first to get asset hashes
        self.asset_hashes = build_static(self.config)
        
        # Check if static assets changed, invalidate post cache if so
        cached_assets_hash = self.lock.get("_metadata", {}).get("_assets_hash")
        current_assets_hash = self._compute_assets_hash()
        
        if cached_assets_hash and cached_assets_hash != current_assets_hash:
            self.logger.info("Static assets changed, invalidating post cache")
            # Clear all post entries but preserve metadata structure
            self.lock = {"_metadata": self.lock.get("_metadata", {})}
        
        # Store metadata
        if "_metadata" not in self.lock:
            self.lock["_metadata"] = {}
        self.lock["_metadata"]["_assets_hash"] = current_assets_hash
        
        build_posts(self.posts, self.config, self.lock, self.asset_hashes)
        
        build_archive(self.posts, self.config, self.asset_hashes)
        build_index(self.posts, self.config, self.asset_hashes)
        build_tags_index(self.posts, self.config, self.asset_hashes)
        build_tags(self.posts, self.config, self.asset_hashes)
        build_errors(self.config, self.asset_hashes)
        
        self.logger.info("Build complete!")
    
    def _compute_assets_hash(self) -> str:
        """Compute hash of current asset filenames for cache invalidation.
        
        Returns:
            MD5 hash of asset filenames mapping
        """
        import json
        
        # Sort items to ensure consistent hashing
        assets_json = json.dumps(self.asset_hashes, sort_keys=True)
        return hashlib.md5(assets_json.encode()).hexdigest()
    
    def _find_markdown_files(self) -> None:
        """Discover all markdown files in posts and pages directories."""
        posts_path = Path(self.config.paths.posts)
        markdown_files = sorted(list(posts_path.rglob("*.md")))
        
        pages_path = Path(self.config.paths.pages) if hasattr(self.config.paths, 'pages') else None
        if pages_path and pages_path.exists():
            page_files = list(pages_path.rglob("*.md"))
            markdown_files.extend(page_files)
        
        for md_file in markdown_files:
            with open(md_file, "r") as f:
                content = f.read()
            file_hash = hashlib.md5(content.encode()).hexdigest()
            self.posts.append(Post(
                path=md_file,
                source=content,
                hash=file_hash
            ))
        
        self.logger.info(f"Found {len(self.posts)} posts")
