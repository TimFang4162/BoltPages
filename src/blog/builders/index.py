"""Index page builder."""

import logging
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from blog.config import Config
from blog.models import Post

logger = logging.getLogger("rich")


def build_index(posts: list[Post], config: Config, assets: dict[str, str]) -> None:
    """Build index page.
    
    Args:
        posts: List of all posts
        config: Blog configuration
        assets: Dictionary mapping original filenames to hashed filenames
    """
    logger.info("Building index.html...")
    
    jinjaenv = Environment(loader=FileSystemLoader(config.paths.templates))
    jinjaenv.globals["SITE_NAME"] = config.site.name
    jinjaenv.globals["ASSETS"] = assets
    
    template = jinjaenv.get_template("index.html")
    
    non_draft_posts = [p for p in posts if not p.is_draft and not p.is_page]
    sorted_posts = sorted(
        non_draft_posts,
        key=lambda p: str(p.post_date),
        reverse=True
    )
    
    html = template.render(posts=sorted_posts)
    output_path = Path(config.build.output_dir) / "index.html"
    
    with open(output_path, "w") as f:
        f.write(html)
