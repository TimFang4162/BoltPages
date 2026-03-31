"""Configuration management with TOML and environment variable support."""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class SiteConfig:
    name: str = "BoltPages"


@dataclass
class BuildConfig:
    cache: bool = True
    log_level: str = "INFO"
    output_dir: str = "build"


@dataclass
class PathsConfig:
    posts: str = "posts"
    pages: str = "pages"
    templates: str = "templates"
    static: str = "static"


@dataclass
class ImagesConfig:
    webp_quality: int = 85


@dataclass
class DevConfig:
    port: int = 8000
    host: str = "127.0.0.1"
    debounce: float = 0.5
    watch_dirs: list[str] = field(default_factory=lambda: ["posts", "templates", "static"])


@dataclass
class Config:
    site: SiteConfig = field(default_factory=SiteConfig)
    build: BuildConfig = field(default_factory=BuildConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    images: ImagesConfig = field(default_factory=ImagesConfig)
    dev: DevConfig = field(default_factory=DevConfig)

    @classmethod
    def load(cls, config_path: str | Path = "config.toml") -> "Config":
        config_path = Path(config_path)
        
        site_config = SiteConfig()
        build_config = BuildConfig()
        paths_config = PathsConfig()
        images_config = ImagesConfig()
        dev_config = DevConfig()
        
        if config_path.exists():
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
            
            if "site" in data:
                site_config = SiteConfig(**data["site"])
            if "build" in data:
                build_config = BuildConfig(**data["build"])
            if "paths" in data:
                paths_config = PathsConfig(**data["paths"])
            if "images" in data:
                images_config = ImagesConfig(**data["images"])
            if "dev" in data:
                dev_config = DevConfig(**data["dev"])
        
        cls._apply_env_overrides(site_config, build_config, paths_config, images_config, dev_config)
        
        return cls(
            site=site_config,
            build=build_config,
            paths=paths_config,
            images=images_config,
            dev=dev_config,
        )
    
    @staticmethod
    def _apply_env_overrides(
        site: SiteConfig,
        build: BuildConfig,
        paths: PathsConfig,
        images: ImagesConfig,
        dev: DevConfig,
    ) -> None:
        if name := os.getenv("BLOG_SITE_NAME"):
            site.name = name
        if cache := os.getenv("BLOG_BUILD_CACHE"):
            build.cache = cache.lower() in ("true", "1", "yes")
        if level := os.getenv("BLOG_BUILD_LOG_LEVEL"):
            build.log_level = level
        if output := os.getenv("BLOG_BUILD_OUTPUT_DIR"):
            build.output_dir = output
        if quality := os.getenv("BLOG_IMAGES_WEBP_QUALITY"):
            images.webp_quality = int(quality)
        if port := os.getenv("BLOG_DEV_PORT"):
            dev.port = int(port)
        if host := os.getenv("BLOG_DEV_HOST"):
            dev.host = host
        if debounce := os.getenv("BLOG_DEV_DEBOUNCE"):
            dev.debounce = float(debounce)
