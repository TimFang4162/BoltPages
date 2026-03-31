# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-17
**Branch:** main
**Type:** Static Blog Generator (Python + Jinja2 + Markdown)

## OVERVIEW

Modern modular static site generator with MD5-based caching, image optimization (WebP), and Chinese UI. Uses a plugin-based architecture with development server support.

## COMMANDS

```bash
# Build site (with cache)
python -m blog build

# Force rebuild (disable cache)
python -m blog build --no-cache

# Development mode (server + file watching + live reload)
python -m blog dev [--port 8000] [--host 127.0.0.1]

# Static file server only
python -m blog server [--port 8000]

# Create new post
mkdir -p posts/$(date +%Y-%m)/post-slug/attachments
touch posts/$(date +%Y-%m)/post-slug/index.md
```

**Installation:**
```bash
pip install -e .
```

**Dependencies:**
- python-frontmatter, minify-html, mistune>=3
- jinja2, pygments, Pillow, rich
- watchdog>=6.0, livereload>=2.7

**Optional (for type checking):**
```bash
pip install -e ".[dev]"  # Includes mypy, types-Pillow
```

## CONFIGURATION

The blog is configured via `config.toml`:

```toml
[site]
name = "BoltPages"

[build]
cache = true
log_level = "INFO"
output_dir = "build"

[paths]
posts = "posts"
templates = "templates"
static = "static"

[images]
webp_quality = 85

[dev]
port = 8000
host = "127.0.0.1"
debounce = 0.5
watch_dirs = ["posts", "templates", "static"]
```

**Environment Variable Overrides:**
- `BLOG_SITE_NAME` - Site name
- `BLOG_BUILD_CACHE` - Enable/disable caching (true/false)
- `BLOG_DEV_PORT` - Development server port
- `BLOG_DEV_DEBOUNCE` - File change debounce delay

## PROJECT STRUCTURE

```
src/blog/
├── __init__.py
├── __main__.py        # CLI entry point
├── cli.py             # Command-line argument parsing
├── config.py          # Configuration management (TOML + env vars)
├── models.py          # Data models (Post, TagCount)
├── builder.py         # Main build orchestrator
├── cache.py           # MD5 cache management
├── assets.py          # Static asset handling and minification
├── devserver.py       # Development server with live reload
├── utils.py           # Logging utilities
├── renderer/
│   ├── markdown.py    # Custom markdown renderer
│   └── typst.py       # Typst compilation
└── builders/
    ├── posts.py       # Post page builder
    ├── archive.py     # Archive page builder
    ├── index.py       # Index page builder
    └── tags.py        # Tag pages builder
```

## CODE STYLE

### Python

| Aspect | Convention |
|--------|------------|
| **Imports** | Standard library first, then third-party (no blank line separator) |
| **Naming** | `snake_case` for functions/variables, `PascalCase` for classes |
| **Type hints** | Full type annotations required (mypy strict mode) |
| **Indentation** | 4 spaces |
| **Line length** | ~100 chars max |
| **Spacing** | No spaces around `=` in default args: `def foo(x: int = 1)` |
| **Comments** | Minimal - code should be self-documenting |

**Error Handling:**
- Log errors with `logger.error()` or `logger.warning()` from rich logging
- Never fail build on recoverable errors (missing images, typst failures)
- Use `try/except` for external operations (file I/O, image conversion, subprocess)
- Return fallback HTML for failed typst compilations

**Logging Pattern:**
```python
from rich.console import Console
from rich.logging import RichHandler
import logging

logging.basicConfig(level="INFO", handlers=[RichHandler(rich_tracebacks=False)])
logger = logging.getLogger("rich")
console = Console()  # For styled output: console.log("[red]error[/red]")
```

### JavaScript

| Aspect | Convention |
|--------|------------|
| **Syntax** | ES6+ (arrow functions, const/let, template literals) |
| **Naming** | `camelCase` for variables/functions |
| **DOM** | Use optional chaining: `document.querySelector('.foo')?.addEventListener(...)` |
| **Events** | Wrap in `DOMContentLoaded` |
| **Comments** | Avoid large commented blocks - delete unused code |

### CSS

| Aspect | Convention |
|--------|------------|
| **Variables** | Use `--name` for colors, fonts, spacing |
| **Naming** | BEM-lite pattern (`component-modifier`, `component__element`) |
| **Theme** | Support `[data-theme="dark"]` selector |
| **Responsive** | Mobile-first, `max-width: 768px` breakpoints |

### Jinja2 Templates

- Always `{% extends "base.html" %}`
- Use blocks: `{% block title %}`, `{% block head %}`, `{% block body %}`
- Markdown content: use `| safe` filter
- UI text: Chinese (首页, 归档, 标签, 复制)

## POST STRUCTURE

**Directory format:** `posts/YYYY-MM/post-name/index.md`
**Attachments:** `posts/YYYY-MM/post-name/attachments/`
**Image refs:** `![](attachments/image.png)` → auto-converts to WebP

**Frontmatter:**
```yaml
---
title: Post Title
date: YYYY-MM-DD
tags:
  - Tag1
  - Tag2
---
```

## KEY FILES

| Task | Location | Notes |
|------|----------|-------|
| Build configuration | config.toml | TOML-based with env overrides |
| Config management | src/blog/config.py | Config dataclass with load() method |
| Main builder | src/blog/builder.py | Builder.build() orchestrates all steps |
| Markdown rendering | src/blog/renderer/markdown.py | MarkdownRenderer class (images, code, TOC, math) |
| Posts builder | src/blog/builders/posts.py | Converts .md to .html |
| Archive builder | src/blog/builders/archive.py | Groups posts by month |
| Tags builder | src/blog/builders/tags.py | Individual tag pages |
| Dev server | src/blog/devserver.py | DevServer with livereload integration |
| CLI entry | src/blog/cli.py | argparse-based command parser |

## BUILD PROCESS

1. `Builder.__init__()` - Initialize with config
2. `Builder.build()` - Main orchestrator
3. `read_lock()` - Load cached MD5 hashes from `build/posts.lock`
4. `_find_markdown_files()` - Discover all `.md` files in `posts/`
5. `restore_metadata_from_cache()` - Skip unchanged posts
6. `build_posts()` - Render markdown to HTML with WebP images
7. `build_archive()`, `build_index()`, `build_tags()`, `build_tags_index()` - Generate pages
8. `build_static()` - Minify CSS/JS, copy static files

**Image handling:** Local images → WebP conversion (quality 85) → `build/assets/{hash}.webp`

## DEVELOPMENT SERVER

The dev server provides:
- **File watching:** Monitors posts/, templates/, static/ directories
- **Auto rebuild:** Rebuilds site on file changes (with 0.5s debounce)
- **Live reload:** Browser automatically refreshes after rebuild

```bash
python -m blog dev
# → Server runs at http://127.0.0.1:8000
# → Edit any file → Auto rebuild → Browser refresh
```

## ANTI-PATTERNS

- Spaces around `=` in default args
- Large commented code blocks (delete instead)
- Failing build on missing images (log and continue)
- Hardcoded file paths (use `Path` objects)
- Import blank lines between stdlib and third-party
- Using `any` as type annotation (use `Any` from typing)

## CONVENTIONS

- No global mutable state (replaced with Builder class)
- Use `Path` objects for all file operations
- Chinese UI strings in templates (no English nav text)
- Code blocks have inline "复制" copy button via script.js
- Type annotations required for all public functions
- Configuration via TOML file with environment variable overrides
