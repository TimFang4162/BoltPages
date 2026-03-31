"""Static assets handling."""

import hashlib
import logging
import minify_html
import shutil
from pathlib import Path

from blog.config import Config

logger = logging.getLogger("rich")


def build_static(config: Config) -> dict[str, str]:
    """Build static files with minification.
    
    Args:
        config: Blog configuration
        
    Returns:
        Dictionary mapping original filenames to hashed filenames
    """
    logger.info("Building static files...")
    
    static_src = Path(config.paths.static)
    output_dir = Path(config.build.output_dir)
    asset_hashes: dict[str, str] = {}
    
    for file_path in static_src.rglob("*"):
        if not file_path.is_file():
            continue
        
        rel_path = file_path.relative_to(static_src)
        dest_path = output_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        if file_path.name == "style.css":
            logger.debug(f"Compressing: {rel_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                css_content = f.read()
            minified_css = minify_css(css_content)
            
            content_hash = hashlib.md5(minified_css.encode()).hexdigest()[:8]
            hashed_filename = f"style-{content_hash}.css"
            hashed_dest_path = dest_path.parent / hashed_filename
            
            with open(hashed_dest_path, "w", encoding="utf-8") as f:
                f.write(minified_css)
            
            asset_hashes["style.css"] = f"/{hashed_filename}"
            
            # Remove old style.css files
            for old_file in output_dir.glob("style-*.css"):
                if old_file.name != hashed_filename:
                    old_file.unlink()
            
        elif file_path.name == "script.js":
            logger.debug(f"Compressing: {rel_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                js_content = f.read()
            minified_js = minify_js(js_content)
            
            content_hash = hashlib.md5(minified_js.encode()).hexdigest()[:8]
            hashed_filename = f"script-{content_hash}.js"
            hashed_dest_path = dest_path.parent / hashed_filename
            
            with open(hashed_dest_path, "w", encoding="utf-8") as f:
                f.write(minified_js)
            
            asset_hashes["script.js"] = f"/{hashed_filename}"
            
            # Remove old script.js files
            for old_file in output_dir.glob("script-*.js"):
                if old_file.name != hashed_filename:
                    old_file.unlink()
            
        elif file_path.name == "hero-particles.js":
            logger.debug(f"Compressing: {rel_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                js_content = f.read()
            minified_js = minify_js(js_content)
            
            content_hash = hashlib.md5(minified_js.encode()).hexdigest()[:8]
            hashed_filename = f"hero-particles-{content_hash}.js"
            hashed_dest_path = dest_path.parent / hashed_filename
            
            with open(hashed_dest_path, "w", encoding="utf-8") as f:
                f.write(minified_js)
            
            asset_hashes["hero-particles.js"] = f"/{hashed_filename}"
            
            # Remove old hero-particles.js files
            for old_file in output_dir.glob("hero-particles-*.js"):
                if old_file.name != hashed_filename:
                    old_file.unlink()
            
        else:
            shutil.copy2(file_path, dest_path)
    
    return asset_hashes


def minify_css(css: str) -> str:
    """Minify CSS content.
    
    Args:
        css: CSS content to minify
        
    Returns:
        Minified CSS
    """
    wrapped = f"<style>{css}</style>"
    minified = minify_html.minify(wrapped, minify_css=True)
    return minified.removeprefix("<style>").removesuffix("</style>")


def minify_js(js: str) -> str:
    """Minify JavaScript content.
    
    Args:
        js: JavaScript content to minify
        
    Returns:
        Minified JavaScript
    """
    wrapped = f"<script>{js}</script>"
    minified = minify_html.minify(wrapped, minify_js=True)
    return minified.removeprefix("<script>").removesuffix("</script>")
