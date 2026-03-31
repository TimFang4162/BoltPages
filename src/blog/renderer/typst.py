"""Typst compilation support."""

import logging
import subprocess

logger = logging.getLogger("rich")


def compile_typst(code: str, typst_config: str) -> str:
    """Compile typst code to SVG with given configuration.
    
    Args:
        code: The typst code to compile
        typst_config: Configuration string to prepend to the code
        
    Returns:
        SVG content or fallback HTML if compilation fails
    """
    full_code = typst_config + "\n" + code
    
    try:
        result = subprocess.run(
            [
                "typst",
                "compile",
                "--features",
                "html",
                "--format",
                "svg",
                "-",  # stdin
                "-",  # stdout
            ],
            input=full_code,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            logger.error(f"Typst compile error: {result.stderr}")
            return f"<pre>{code}</pre>"
    except Exception as e:
        logger.error(f"Typst error: {e}")
        return f"<pre>{code}</pre>"
