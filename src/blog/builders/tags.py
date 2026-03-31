"""Tags page builder."""

import logging
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from blog.config import Config
from blog.models import Post

logger = logging.getLogger("rich")


def aggregate_tags(posts: list[Post]) -> dict[str, int]:
    """Aggregate tag counts from all posts.
    
    Args:
        posts: List of all posts
        
    Returns:
        Dictionary mapping tag names to counts
    """
    tag_counts: dict[str, int] = {}
    for post in posts:
        if post.is_draft or post.is_page:
            continue
        tags = post.tags
        for tag in tags:
            if tag in tag_counts:
                tag_counts[tag] += 1
            else:
                tag_counts[tag] = 1
    return dict(sorted(tag_counts.items()))


def build_tags_index(posts: list[Post], config: Config, assets: dict[str, str]) -> None:
    """Build tags index page.
    
    Args:
        posts: List of all posts
        config: Blog configuration
        assets: Dictionary mapping original filenames to hashed filenames
    """
    logger.info("Building tags index...")
    
    jinjaenv = Environment(loader=FileSystemLoader(config.paths.templates))
    jinjaenv.globals["SITE_NAME"] = config.site.name
    jinjaenv.globals["ASSETS"] = assets
    
    tag_counts = aggregate_tags(posts)
    template = jinjaenv.get_template("tags.html")
    
    html = template.render(tags=tag_counts)
    output_path = Path(config.build.output_dir) / "tags.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write(html)


def build_tags(posts: list[Post], config: Config, assets: dict[str, str]) -> None:
    """Build individual tag pages.
    
    Args:
        posts: List of all posts
        config: Blog configuration
        assets: Dictionary mapping original filenames to hashed filenames
    """
    logger.info("Building tag pages...")
    
    jinjaenv = Environment(loader=FileSystemLoader(config.paths.templates))
    jinjaenv.globals["SITE_NAME"] = config.site.name
    jinjaenv.globals["ASSETS"] = assets
    
    tag_counts = aggregate_tags(posts)
    template = jinjaenv.get_template("tag.html")
    tags_dir = Path(config.build.output_dir) / "tags"
    tags_dir.mkdir(parents=True, exist_ok=True)
    
    for tag in tag_counts:
        tag_posts: list[Post] = []
        for post in posts:
            if post.is_draft or post.is_page:
                continue
            post_tags = post.tags
            if tag in post_tags:
                tag_posts.append(post)
        
        tag_posts = sorted(
            tag_posts,
            key=lambda p: str(p.post_date),
            reverse=True,
        )
        
        output_path = tags_dir / f"{tag}.html"
        
        html = template.render(
            posts=tag_posts,
            page_title=f"标签: {tag}",
            header_title=f"标签: {tag}",
            view_mode="list",
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            f.write(html)
