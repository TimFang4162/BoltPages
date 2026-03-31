"""Mermaid diagram compilation support."""

import logging
import subprocess

logger = logging.getLogger("rich")


def compile_mermaid(code: str) -> str:
    """Compile mermaid code to SVG.
    
    Args:
        code: The mermaid diagram code
        
    Returns:
        SVG content or fallback HTML if compilation fails
    """
    try:
        result = subprocess.run(
            [
                "mmdr",
                "-e",
                "svg",
                "-c",
                "mermaid.config.json"
            ],
            input=code,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            logger.error(f"Mermaid compile error: {result.stderr}")
            return f"<pre>{code}</pre>"
    except Exception as e:
        logger.error(f"Mermaid error: {e}")
        return f"<pre>{code}</pre>"
