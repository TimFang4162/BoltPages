"""Archive page builder."""

import logging
import math
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from blog.config import Config
from blog.models import Post

logger = logging.getLogger("rich")


def calculate_stats(posts: list[Post]) -> tuple[int, int, dict[str, dict[str, int]], dict[str, list[int]]]:
    """Calculate archive statistics.
    
    Args:
        posts: List of all posts
        
    Returns:
        Tuple of (total_posts, total_words, monthly_stats, yearly_heatmap)
        - monthly_stats: {year_month: {count, words}}
        - yearly_heatmap: {year: [12 month counts]}
    """
    sorted_posts = sorted(
        [p for p in posts if not p.is_draft and not p.is_page],
        key=lambda p: str(p.post_date),
        reverse=False
    )
    
    total_posts = len(sorted_posts)
    total_words = sum(len(p.content) for p in sorted_posts)
    
    monthly_stats: dict[str, dict[str, int]] = {}
    for post in sorted_posts:
        date_val = post.post_date
        if date_val:
            try:
                if isinstance(date_val, str):
                    date_obj = datetime.strptime(date_val, "%Y-%m-%d")
                else:
                    date_obj = date_val
                year_month = date_obj.strftime("%Y-%m")
            except ValueError:
                continue
            
            if year_month not in monthly_stats:
                monthly_stats[year_month] = {"count": 0, "words": 0}
            monthly_stats[year_month]["count"] += 1
            monthly_stats[year_month]["words"] += len(post.content)
    
    yearly_heatmap: dict[str, list[int]] = {}
    for year_month, data in monthly_stats.items():
        year = year_month[:4]
        month = int(year_month[5:7]) - 1
        if year not in yearly_heatmap:
            yearly_heatmap[year] = [0] * 12
        yearly_heatmap[year][month] = data["count"]
    
    return total_posts, total_words, monthly_stats, yearly_heatmap


def calculate_y_ticks(max_value: float) -> list[dict]:
    """Calculate 4-5 evenly spaced Y axis ticks.
    
    Args:
        max_value: Maximum value to scale
        
    Returns:
        List of {value, percent} dicts
    """
    if max_value == 0:
        return [{"value": 0, "percent": 0}]
    
    raw_step = max_value / 4
    magnitude = 10 ** math.floor(math.log10(raw_step))
    normalized = raw_step / magnitude
    
    if normalized <= 1:
        step = magnitude
    elif normalized <= 2:
        step = 2 * magnitude
    elif normalized <= 5:
        step = 5 * magnitude
    else:
        step = 10 * magnitude
    
    ticks = []
    current = 0
    while current <= max_value * 1.05:
        ticks.append({
            "value": current,
            "percent": (current / max_value) * 100 if max_value > 0 else 0
        })
        current += step
    
    return ticks


def sample_x_labels(data_points: list) -> list:
    """Sample x-axis labels to avoid overcrowding.
    
    Args:
        data_points: List of data point dicts
        
    Returns:
        List of (index, point) tuples
    """
    n = len(data_points)
    if n <= 8:
        return [(i, p) for i, p in enumerate(data_points)]
    
    target_count = 8
    step = (n - 1) / (target_count - 1)
    
    sampled = []
    for i in range(target_count):
        idx = round(i * step)
        if idx < n:
            sampled.append((idx, data_points[idx]))
    
    return sampled


def generate_line_chart(monthly_stats: dict[str, dict[str, int]]) -> dict:
    """Generate SVG line chart data for HTML/CSS rendering.
    
    Args:
        monthly_stats: {year_month: {count, words}}
        
    Returns:
        dict with keys:
        - svg_path: SVG path d attribute string
        - data_points: list of {x_percent, y_percent, label, value}
        - max_value: maximum value for Y axis
        - y_ticks: list of {value, percent}
        - x_labels: list of (index, point) tuples
    """
    if not monthly_stats:
        return {"svg_path": "", "data_points": [], "max_value": 0, "y_ticks": [], "x_labels": []}
    
    sorted_months = sorted(monthly_stats.keys())
    if len(sorted_months) < 2:
        return {"svg_path": "", "data_points": [], "max_value": 0, "y_ticks": [], "x_labels": []}
    
    words = [monthly_stats[m]["words"] for m in sorted_months]
    
    cumulative_words = []
    total_w = 0
    for w in words:
        total_w += w
        cumulative_words.append(total_w)
    
    words_k = [w / 1000 for w in cumulative_words]
    max_value = max(words_k) if words_k else 0
    
    if max_value == 0:
        return {"svg_path": "", "data_points": [], "max_value": 0, "y_ticks": [], "x_labels": []}
    
    n = len(sorted_months)
    padding = 10  # 左右各留10%空白
    data_points = []
    for i, (month, value) in enumerate(zip(sorted_months, words_k)):
        x_percent = padding + (i / (n - 1)) * (100 - 2 * padding) if n > 1 else 50
        y_percent = (value / max_value) * 100
        label = month[5:] + "月" if len(month) == 7 else month
        data_points.append({
            "x_percent": x_percent,
            "y_percent": y_percent,
            "label": label,
            "value": value
        })
    
    points = []
    for p in data_points:
        points.append(f"{p['x_percent']:.1f},{100 - p['y_percent']:.1f}")
    svg_path = "M" + " L".join(points)
    
    y_ticks = calculate_y_ticks(max_value)
    x_labels = sample_x_labels(data_points)
    
    return {
        "svg_path": svg_path,
        "data_points": data_points,
        "max_value": max_value,
        "y_ticks": y_ticks,
        "x_labels": x_labels
    }


def generate_heatmap(yearly_heatmap: dict[str, list[int]]) -> str:
    """Generate HTML table for yearly heatmap.
    
    Args:
        yearly_heatmap: {year: [12 month counts]}
        
    Returns:
        HTML string
    """
    if not yearly_heatmap:
        return ""
    
    years = sorted(yearly_heatmap.keys(), reverse=True)
    months = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
    
    all_counts = [c for year_data in yearly_heatmap.values() for c in year_data]
    max_count = max(all_counts) if all_counts else 1
    
    def get_level(count: int) -> str:
        if count == 0:
            return "level-0"
        ratio = count / max_count
        if ratio <= 0.25:
            return "level-1"
        elif ratio <= 0.5:
            return "level-2"
        elif ratio <= 0.75:
            return "level-3"
        return "level-4"
    
    rows = []
    for year in years:
        cells = "".join(
            # f'<td class="heatmap-cell {get_level(yearly_heatmap[year][m])}">{yearly_heatmap[year][m]}</td>'
            f'<td class="heatmap-cell {get_level(yearly_heatmap[year][m])}"></td>'
            for m in range(12)
        )
        rows.append(f"<tr><th>{year}</th>{cells}</tr>")
    
    header = "<tr><th>年\月</th>" + "".join(f"<th>{m}</th>" for m in months) + "</tr>"
    
    return f'<table class="heatmap"><thead>{header}</thead><tbody>{"".join(rows)}</tbody></table>'


def build_archive(posts: list[Post], config: Config, assets: dict[str, str]) -> None:
    """Build archive page grouped by month.
    
    Args:
        posts: List of all posts
        config: Blog configuration
        assets: Dictionary mapping original filenames to hashed filenames
    """
    logger.info("Building archive...")
    
    jinjaenv = Environment(loader=FileSystemLoader(config.paths.templates))
    jinjaenv.globals["SITE_NAME"] = config.site.name
    jinjaenv.globals["ASSETS"] = assets
    
    def format_words(w: int) -> str:
        if w >= 1000:
            return f"{w / 1000:.1f}k"
        return str(w)
    
    jinjaenv.filters["format_words"] = format_words
    
    template = jinjaenv.get_template("archive.html")
    
    sorted_posts = sorted(
        [p for p in posts if not p.is_draft and not p.is_page],
        key=lambda p: str(p.post_date),
        reverse=True
    )
    
    grouped: dict[str, list[Post]] = {}
    for post in sorted_posts:
        date_val = post.post_date
        if date_val:
            try:
                if isinstance(date_val, str):
                    date_obj = datetime.strptime(date_val, "%Y-%m-%d")
                else:
                    date_obj = date_val
                year_month = date_obj.strftime("%Y年%m月")
            except ValueError:
                continue
            
            if year_month not in grouped:
                grouped[year_month] = []
            grouped[year_month].append(post)
    
    total_posts, total_words, monthly_stats, yearly_heatmap = calculate_stats(posts)
    
    chart_data = generate_line_chart(monthly_stats)
    heatmap_html = generate_heatmap(yearly_heatmap)
    
    html = template.render(
        grouped=grouped,
        total_posts=total_posts,
        total_words=total_words,
        chart_data=chart_data,
        heatmap_html=heatmap_html
    )
    output_path = Path(config.build.output_dir) / "archive.html"
    
    with open(output_path, "w") as f:
        f.write(html)
