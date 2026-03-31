"""Post page builder."""

import logging
import shutil
from datetime import date, datetime as dt_datetime
from typing import Any

import frontmatter
import mistune
import minify_html
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from blog.cache import AssetRegistry, write_lock
from blog.config import Config
from blog.models import Post
from blog.renderer.markdown import MarkdownRenderer

logger = logging.getLogger("rich")


def build_posts(posts: list[Post], config: Config, lock: dict[str, dict[str, Any]], assets: dict[str, str] | None = None) -> None:
    """Build all post pages.
    
    Args:
        posts: List of all posts
        config: Blog configuration
        lock: Cache lock dictionary
        assets: Dictionary mapping original filenames to hashed filenames
    """
    logger.info("Building posts...")
    
    jinjaenv = Environment(loader=FileSystemLoader(config.paths.templates))
    jinjaenv.globals["SITE_NAME"] = config.site.name
    jinjaenv.globals["ASSETS"] = assets or {}
    
    template = jinjaenv.get_template("post.html")
    assets_dir = Path(config.build.output_dir) / "assets"
    cache_changed = False
    asset_registry = AssetRegistry()
    
    for post in posts:
        metadata_obj = frontmatter.loads(post.source)
        post.metadata = metadata_obj.metadata
        post.content = metadata_obj.content
    
    def get_date(post: Post) -> date:
        d = post.metadata.get("date", "")
        if isinstance(d, date):
            return d
        if isinstance(d, str) and d:
            return dt_datetime.strptime(d, "%Y-%m-%d").date()
        return date.min
    
    sorted_posts = sorted(posts, key=get_date, reverse=True)
    published_posts = [p for p in sorted_posts if not p.is_draft and not p.is_page]
    post_map = {post.path: post for post in sorted_posts}
    
    for post in sorted_posts:
        if post.hash in lock and config.build.cache:
            logger.debug(f"Skipping {post.path} (cached)")
            continue
        
        logger.info(f"Building {post.path}...")
        
        _update_lock(post, lock)
        cache_changed = True
        
        if post.is_draft:
            logger.debug(f"Skipping draft: {post.path}")
            continue
        
        is_page = post.is_page
        if is_page and not post.slug:
            logger.warning(f"Page {post.path} has no slug, skipping")
            continue
        
        renderer = MarkdownRenderer(current_post=post, use_cache=config.build.cache, assets_dir=assets_dir, asset_registry=asset_registry)
        md = mistune.create_markdown(
            renderer=renderer,
            hard_wrap=True,
            plugins=["strikethrough", "footnotes", "table", "url", "task_lists", "math"],
        )
        
        renderer.markdown_parser = md
        
        html_content = md(post.content)
        
        if is_page:
            prev_post = None
            next_post = None
        else:
            idx = published_posts.index(post)
            prev_post = published_posts[idx + 1] if idx + 1 < len(published_posts) else None
            next_post = published_posts[idx - 1] if idx - 1 >= 0 else None
        
        html = template.render(
            content=html_content,
            metadata=post.metadata,
            toc_data=renderer.toc_data,
            prev_post=prev_post,
            next_post=next_post
        )
        
        minified = minify_html.minify(
            html, minify_css=True, remove_processing_instructions=True
        )
        
        if is_page and post.slug:
            output_path = Path(config.build.output_dir) / f"{post.slug.lstrip('/')}.html"
        else:
            output_path = Path(config.build.output_dir) / post.path.with_suffix(".html")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            f.write(minified)
        
        _copy_attachments(post, config)
    
    if cache_changed and config.build.cache:
        write_lock(lock)
        asset_registry.cleanup_orphaned(assets_dir)


def _update_lock(post: Post, lock: dict[str, dict[str, Any]]) -> None:
    """Update post metadata in cache lock.
    
    Args:
        post: Post to save
        lock: Lock dictionary to update
    """
    lock_metadata = {}
    for key, value in post.metadata.items():
        if isinstance(value, (str, int, float, bool, list, dict, type(None))):
            lock_metadata[key] = value
        else:
            lock_metadata[key] = str(value)
    
    lock[post.hash] = {"path": str(post.path), "metadata": lock_metadata}


def _copy_attachments(post: Post, config: Config) -> None:
    """Copy attachments directory to output if exists.
    
    Args:
        post: Post object
        config: Blog configuration
    """
    attachments_dir = post.path.parent / "attachments"
    if not attachments_dir.exists() or not attachments_dir.is_dir():
        return
    
    output_dir = Path(config.build.output_dir) / attachments_dir
    
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    shutil.copytree(attachments_dir, output_dir)
    
    file_count = len([f for f in output_dir.rglob("*") if f.is_file()])
    logger.info(f"Copied {file_count} attachment(s) from {post.path.parent.name}/")
