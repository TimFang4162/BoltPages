"""Error pages builder."""

import logging
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from blog.config import Config

logger = logging.getLogger("rich")


def build_errors(config: Config, assets: dict[str, str]) -> None:
    """Build error pages.
    
    Args:
        config: Blog configuration
        assets: Dictionary mapping original filenames to hashed filenames
    """
    logger.info("Building error pages...")
    
    jinjaenv = Environment(loader=FileSystemLoader(config.paths.templates))
    jinjaenv.globals["SITE_NAME"] = config.site.name
    jinjaenv.globals["ASSETS"] = assets
    
    template = jinjaenv.get_template("404.html")
    html = template.render()
    output_path = Path(config.build.output_dir) / "404.html"
    
    with open(output_path, "w") as f:
        f.write(html)
