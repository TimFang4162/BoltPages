"""Cache management for build artifacts."""

import json
import logging
from pathlib import Path
from typing import Any

from blog.models import Post

logger = logging.getLogger("rich")

CACHE_VERSION = "1.0"


class AssetRegistry:
    """Registry for tracking build assets."""
    
    def __init__(self) -> None:
        """Initialize asset registry."""
        self.assets: set[str] = set()
    
    def register(self, asset_path: str) -> None:
        """Register an asset as used.
        
        Args:
            asset_path: Asset path relative to assets directory
        """
        self.assets.add(asset_path)
    
    def cleanup_orphaned(self, assets_dir: Path) -> int:
        """Remove orphaned assets not in registry.
        
        Args:
            assets_dir: Path to assets directory
            
        Returns:
            Number of files removed
        """
        if not assets_dir.exists():
            return 0
        
        removed = 0
        for asset_file in assets_dir.iterdir():
            if asset_file.name not in self.assets:
                try:
                    asset_file.unlink()
                    removed += 1
                    logger.debug(f"Removed orphaned asset: {asset_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to remove {asset_file.name}: {e}")
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} orphaned asset(s)")
        
        return removed


def read_lock(use_cache: bool = True) -> dict[str, dict[str, Any]]:
    """Read cache lock from disk.
    
    Args:
        use_cache: Whether to use caching
        
    Returns:
        Dictionary mapping file hashes to metadata (with _metadata entry)
    """
    if not use_cache:
        return {}
    
    try:
        with open("build/posts.lock", "r") as f:
            data = json.load(f)
            
            if data.get("_version") != CACHE_VERSION:
                logger.info("Cache version mismatch, rebuilding cache")
                return {}
            
            # Merge posts and metadata for in-memory use
            result = data.get("posts", {})
            if "_metadata" in data:
                result["_metadata"] = data["_metadata"]
            
            return result
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        logger.warning("Cache file corrupted, ignoring")
        return {}


def write_lock(lock: dict[str, dict[str, Any]]) -> None:
    """Write cache lock to disk atomically.
    
    Args:
        lock: Cache lock dictionary to write (may contain _metadata)
    """
    Path("build").mkdir(parents=True, exist_ok=True)
    
    # Extract metadata if present
    metadata = lock.pop("_metadata", {})
    
    data = {
        "_version": CACHE_VERSION,
        "_metadata": metadata,
        "posts": lock
    }
    
    temp_path = Path("build/posts.lock.tmp")
    with open(temp_path, "w") as f:
        json.dump(data, f, indent=4)
    
    temp_path.replace("build/posts.lock")


def restore_metadata_from_cache(posts: list[Post], lock: dict[str, dict[str, Any]], use_cache: bool = True) -> None:
    """Restore post metadata from cache.
    
    Args:
        posts: List of all posts
        lock: Cache lock dictionary (may contain _metadata entry)
        use_cache: Whether to use caching
    """
    if not use_cache:
        return
    
    for post in posts:
        if post.hash in lock and isinstance(lock[post.hash], dict):
            post.metadata = lock[post.hash].get("metadata", {})
