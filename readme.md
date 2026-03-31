# BoltPages

`BoltPages` is a static blog generator written in Python.

This repository is an archived, sanitized snapshot of the project. It keeps the generator itself, a minimal set of example content, and the original template/rendering pipeline.

## Features

- Markdown rendering with custom extensions
- Typst math rendering
- Mermaid diagram support
- Static asset processing and minification
- WebP image conversion
- Incremental build cache
- Development server with live reload

## Install

```sh
pip install -e .
```

Optional development dependencies:

```sh
pip install -e ".[dev]"
```

## Usage

Build the site:

```sh
python -m blog build
```

Force a full rebuild:

```sh
python -m blog build --no-cache
```

Run the development server:

```sh
python -m blog dev
```

Serve the generated output only:

```sh
python -m blog server
```

## Project Layout

- `src/blog/`: core generator code
- `templates/`: Jinja2 templates
- `static/`: static assets
- `posts/`: example posts
- `pages/`: standalone pages

## Notes

- The repository history was cleaned before archival.
- Content was reduced to a small example set.
- Sensitive personal material and obsolete assets were removed.
