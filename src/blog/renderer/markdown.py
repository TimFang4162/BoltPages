"""Markdown rendering with custom extensions."""

import hashlib
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

import mistune
from mistune.util import escape as escape_text
from mistune.util import safe_entity, striptags
from PIL import Image
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from blog.cache import AssetRegistry
from blog.models import Post
from blog.renderer.mermaid import compile_mermaid
from blog.renderer.typst import compile_typst
from mistune import Markdown as MarkdownParser

logger = logging.getLogger("rich")


class MarkdownRenderer(mistune.HTMLRenderer):
    """Custom markdown renderer with image optimization, code highlighting, and math support."""
    
    def __init__(self, current_post: Post, use_cache: bool = True, assets_dir: Path = Path("build/assets"), asset_registry: Optional[AssetRegistry] = None) -> None:
        super().__init__()
        self.current_post = current_post
        self.use_cache = use_cache
        self.assets_dir = assets_dir
        self.asset_registry = asset_registry
        self.toc_data: list[dict[str, Any]] = []
        self.heading_stack: list[str] = []
        self.markdown_parser: Optional[MarkdownParser] = None
    
    def heading(self, text: str, level: int, **attrs: Any) -> str:
        plain_text = re.sub(r"<[^>]+>", "", text)
        
        self.heading_stack = self.heading_stack[:level - 1]
        self.heading_stack.append(plain_text)
        
        path_text = " > ".join(self.heading_stack)
        content_hash = hashlib.md5(path_text.encode("utf-8")).hexdigest()[:8]
        section_id = f"h{content_hash}"
        
        self.toc_data.append({"id": section_id, "text": plain_text, "level": level})
        
        return f'<h{str(level)} id="{section_id}">{text}<button class="header-anchor-btn" onclick="copyHeadingLink(&quot;{section_id}&quot;)" title="复制链接">#</button></h{str(level)}>\n'
    
    def _wrap_image_with_caption(self, img_tag: str, alt: str) -> str:
        if alt and alt.strip():
            return f'<figure class="image-caption">{img_tag}<figcaption>{alt}</figcaption></figure>'
        return img_tag
    
    def image(self, text: str, url: str, title: Optional[str] = None) -> str:
        src = self.safe_url(url)
        alt = escape_text(striptags(text))
        
        logger.debug(
            f"Rendering image: {'url=' + src if src else ''} {'alt=' + alt if alt else ''} {'title=' + title if title else ''}"
        )
        
        if src.startswith("http://") or src.startswith("https://"):
            img_tag = f'<img src="{src}" alt="{escape_text(alt)}" loading="lazy" decoding="async"></img>'
            return self._wrap_image_with_caption(img_tag, alt)
        
        post_dir = self.current_post.path.parent
        image_path = post_dir / src
        
        if image_path.exists():
            if image_path.suffix.lower() == ".svg":
                return self._handle_svg(image_path, alt)
            if image_path.suffix.lower() == ".gif":
                return self._handle_gif(image_path, alt)
            return self._handle_raster_image(image_path, alt)
        else:
            logger.error(f"Image not found: {image_path}")
        
        img_tag = f'<img src="{src}" alt="{alt}" loading="lazy" decoding="async"></img>'
        return self._wrap_image_with_caption(img_tag, alt)
    
    def _handle_svg(self, image_path: Path, alt: str) -> str:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image_hash = hashlib.md5(image_bytes).hexdigest()
        svg_path = self.assets_dir / f"{image_hash}.svg"
        asset_url = f"/assets/{image_hash}.svg"
        
        if self.asset_registry:
            self.asset_registry.register(f"{image_hash}.svg")
        
        if not svg_path.exists():
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            with open(svg_path, "wb") as f:
                f.write(image_bytes)
            logger.debug(f"Copied SVG: {image_path.name} -> {image_hash}.svg")
        else:
            logger.debug(f"Using cached SVG: {image_path.name} -> {image_hash}.svg")
        
        img_tag = f'<img src="{asset_url}" alt="{alt}" loading="lazy" decoding="async"></img>'
        return self._wrap_image_with_caption(img_tag, alt)
    
    def _handle_gif(self, image_path: Path, alt: str) -> str:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image_hash = hashlib.md5(image_bytes).hexdigest()
        gif_path = self.assets_dir / f"{image_hash}.gif"
        asset_url = f"/assets/{image_hash}.gif"
        
        if self.asset_registry:
            self.asset_registry.register(f"{image_hash}.gif")
        
        if gif_path.exists():
            logger.debug(f"Using cached GIF: {image_path.name} -> {image_hash}.gif")
        else:
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            with open(gif_path, "wb") as f:
                f.write(image_bytes)
            logger.debug(f"Copied GIF: {image_path.name} -> {image_hash}.gif")
        
        img_tag = f'<img src="{asset_url}" alt="{alt}" loading="lazy" decoding="async"></img>'
        return self._wrap_image_with_caption(img_tag, alt)
    
    def _handle_raster_image(self, image_path: Path, alt: str) -> str:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        img = Image.open(image_path)
        width, height = img.size
        
        image_hash = hashlib.md5(image_bytes).hexdigest()
        webp_path = self.assets_dir / f"{image_hash}.webp"
        asset_url = f"/assets/{image_hash}.webp"
        
        if self.asset_registry:
            self.asset_registry.register(f"{image_hash}.webp")
        
        if webp_path.exists():
            logger.debug(f"Using cached image for: {image_path.name} -> {image_hash}.webp")
            img_tag = f'<img src="{asset_url}" alt="{alt}" width="{width}" height="{height}" loading="lazy" decoding="async"></img>'
            return self._wrap_image_with_caption(img_tag, alt)
        
        try:
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            img.save(webp_path, "WEBP", quality=85)
            img_tag = f'<img src="{asset_url}" alt="{alt}" width="{width}" height="{height}" loading="lazy" decoding="async"></img>'
            return self._wrap_image_with_caption(img_tag, alt)
        except Exception as e:
            logger.error(f"Error converting {image_path}: {e}")
        
        img_tag = f'<img src="{image_path}" alt="{alt}" loading="lazy" decoding="async"></img>'
        return self._wrap_image_with_caption(img_tag, alt)
    
    def block_code(self, code: str, info: Optional[str] = None) -> str:
        formatter = HtmlFormatter(
            linenos="inline",
            cssclass="highlight",
            linespans="line",
            style="github-dark",
        )
        
        if info is not None:
            info = info.strip()
        
        should_wrap = False
        display_info = info
        
        if info:
            parts = info.split()
            lang = parts[0]
            
            if "wrap" in parts[1:]:
                should_wrap = True
                display_info = " ".join([p for p in parts if p != "wrap"])
            
            if lang == "typst":
                return self._handle_typst(code, info)
            
            if lang == "mermaid":
                return self._handle_mermaid(code, info)
            
            if lang == "details":
                return self._handle_details(code, info)
            
            try:
                lexer = get_lexer_by_name(lang, stripall=True)
            except Exception:
                logger.warning(f"Unknown language for syntax highlighting: {info}")
                lexer = get_lexer_by_name("text", stripall=True)
        else:
            logger.warning("No language specified for code block.")
            lexer = get_lexer_by_name("text", stripall=True)
        
        result = highlight(code, lexer, formatter)
        wrap_class = " highlight-wrap" if should_wrap else ""
        return f'<div class="highlight-container"><div class="highlight-banner"><span class="highlight-info"><span class="icon--mdi icon--mdi--code icon_14px"></span>{display_info if display_info else ""}</span><button class="copy-btn"><span class="icon--mdi icon--mdi--content-copy icon_14px"></span>复制</button></div><div class="highlight-content{wrap_class}">{result}</div></div>\n'
    
    def _handle_typst(self, code: str, info: str) -> str:
        code_hash = hashlib.md5(code.encode()).hexdigest()
        
        logger.debug(f"Compiling typst: {code_hash}")
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        svg_desktop = self.assets_dir / f"{code_hash}_desktop.svg"
        svg_mobile = self.assets_dir / f"{code_hash}_mobile.svg"
        
        if self.asset_registry:
            self.asset_registry.register(f"{code_hash}_desktop.svg")
            self.asset_registry.register(f"{code_hash}_mobile.svg")
        
        if svg_desktop.exists() and svg_mobile.exists() and self.use_cache:
            logger.debug(f"Using cached typst for: {code_hash}")
            svg_desktop_content = svg_desktop.read_text(encoding="utf-8")
            svg_mobile_content = svg_mobile.read_text(encoding="utf-8")
        else:
            config_desktop = "#set page(fill:none,height:auto,margin:8pt,width:600pt)\n#set text(size: 14pt)"
            config_mobile = "#set page(fill:none,height:auto,margin:8pt,width:350pt)\n#set text(size: 14pt)"
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_desktop = executor.submit(compile_typst, code, config_desktop)
                future_mobile = executor.submit(compile_typst, code, config_mobile)
                
                svg_desktop_content = future_desktop.result()
                svg_mobile_content = future_mobile.result()
            
            if svg_desktop_content and not svg_desktop_content.startswith("<pre>"):
                svg_desktop.write_text(svg_desktop_content, encoding="utf-8")
            if svg_mobile_content and not svg_mobile_content.startswith("<pre>"):
                svg_mobile.write_text(svg_mobile_content, encoding="utf-8")
        
        result = f'<picture class="typst-picture">\
            <img class="typst-desktop" src="/assets/{code_hash}_desktop.svg">\
            <img class="typst-mobile" src="/assets/{code_hash}_mobile.svg">\
        </picture>'
        return f'<div class="highlight-container"><div class="highlight-banner"><span class="highlight-info"><span class="icon--mdi icon--mdi--code icon_14px"></span>{info}</span></div><div class="highlight-content">{result}</div></div>\n'
    
    def _handle_mermaid(self, code: str, info: str) -> str:
        code_hash = hashlib.md5(code.encode()).hexdigest()
        
        logger.debug(f"Compiling mermaid: {code_hash}")
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        svg_path = self.assets_dir / f"{code_hash}_mermaid.svg"
        
        if self.asset_registry:
            self.asset_registry.register(f"{code_hash}_mermaid.svg")
        
        if svg_path.exists() and self.use_cache:
            logger.debug(f"Using cached mermaid for: {code_hash}")
            svg_content = svg_path.read_text(encoding="utf-8")
        else:
            svg_content = compile_mermaid(code)
            
            if svg_content and not svg_content.startswith("<pre>"):
                svg_path.write_text(svg_content, encoding="utf-8")
        
        result = f'<div class="mermaid-wrapper"><img class="mermaid-diagram" src="/assets/{code_hash}_mermaid.svg" alt="{escape_text(info)}" loading="lazy" decoding="async"></div>'
        return f'<div class="highlight-container"><div class="highlight-banner"><span class="highlight-info"><span class="icon--mdi icon--mdi--graph-line icon_14px"></span>{info}</span></div><div class="highlight-content">{result}</div></div>\n'
    
    def _parse_details_params(self, info: str) -> tuple[str, str]:
        """Parse details code block info string.
        
        Args:
            info: Info string like 'details summary="Click to expand"'
            
        Returns:
            Tuple of (summary_text, remaining_info)
        """
        import re
        
        summary_match = re.search(r'summary=["\']([^"\']+)["\']', info)
        summary = summary_match.group(1) if summary_match else "Click to expand"
        
        remaining_info = info
        if summary_match:
            remaining_info = remaining_info[:summary_match.start()] + remaining_info[summary_match.end():]
        remaining_info = remaining_info.replace("details", "").strip()
        
        return summary, remaining_info
    
    def _handle_details(self, code: str, info: str) -> str:
        """Handle details collapsible block.
        
        Args:
            code: The markdown content inside the details block
            info: Info string like 'details summary="Click to expand"'
            
        Returns:
            HTML string with <details> tag
        """
        summary, remaining_attrs = self._parse_details_params(info)
        
        if not self.markdown_parser:
            logger.warning("No markdown parser available, rendering details as code block")
            return f'<div class="highlight-container"><pre><code>{escape_text(code)}</code></pre></div>'
        
        rendered_content = self.markdown_parser(code)
        
        attrs_html = f' {remaining_attrs}' if remaining_attrs else ''
        
        return f'<details class="doc-details"{attrs_html}><summary class="doc-summary">{summary}</summary><div class="doc-details-content">{rendered_content}</div></details>'
    
    def block_math(self, text: str) -> str:
        math_hash = hashlib.md5(text.encode()).hexdigest()
        svg_path = self.assets_dir / f"{math_hash}_math.svg"
        
        if self.asset_registry:
            self.asset_registry.register(f"{math_hash}_math.svg")
        
        if svg_path.exists() and self.use_cache:
            logger.debug(f"Using cached math: {math_hash}")
            result = svg_path.read_text(encoding="utf-8")
        else:
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            result = compile_typst(f"${text}$", "#set page(fill:none,height:auto,margin:8pt,width:auto)\n#set text(size: 14pt)")
            
            if result and not result.startswith("<pre>"):
                svg_path.write_text(result, encoding="utf-8")
        
        return f'<div class="math-block">{result}</div>'
    
    def inline_math(self, text: str) -> str:
        math_hash = hashlib.md5(text.encode()).hexdigest()
        svg_path = self.assets_dir / f"{math_hash}_math.svg"
        
        if self.asset_registry:
            self.asset_registry.register(f"{math_hash}_math.svg")
        
        if svg_path.exists() and self.use_cache:
            logger.debug(f"Using cached math: {math_hash}")
            result = svg_path.read_text(encoding="utf-8")
        else:
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            result = compile_typst(f"${text}$", "#set page(fill:none,height:auto,margin:8pt,width:auto)\n#set text(size: 14pt)")
            
            if result and not result.startswith("<pre>"):
                svg_path.write_text(result, encoding="utf-8")
        
        return f'<span class="math-inline">{result}</span>'
    
    def link(self, text: str, url: str, title: Optional[str] = None) -> str:
        url = self.safe_url(url)
        return f'<a href="{url}" {f" title={escape_text(title)}" if title else ""}><span class="icon--mdi icon--mdi--link-variant icon_14px icon_link"></span>{text}</a>'
