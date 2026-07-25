"""Generates funny cartoon images using Gemini API (primary) with Pollinations.ai fallback.

Image generation pipeline:
  1. Try Gemini API (high quality, needs GEMINI_API_KEY)
  2. Fall back to Pollinations.ai (free, no key needed)
"""
import hashlib
import logging
import time
from datetime import datetime
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import URLError

from config import (
    CARTOON_DIR,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_IMAGE_SIZE,
    POLLINATIONS_BASE_URL,
    build_filename,
)

logger = logging.getLogger(__name__)


def generate_cartoon(comedy_analysis: dict[str, Any]) -> dict[str, Any] | None:
    """Generate a funny cartoon image from the comedy analysis.

    Tries Gemini API first (higher quality). Falls back to Pollinations.ai if
    Gemini key is not set or fails.
    Returns metadata about the generated image.
    """
    cartoon_prompt = comedy_analysis.get("cartoon_prompt", "")
    title = comedy_analysis.get("title", "unknown")
    one_liner = comedy_analysis.get("one_liner", "")
    article_url = comedy_analysis.get("article_url", "")

    if not cartoon_prompt:
        logger.warning("No cartoon prompt available; skipping image generation.")
        return None

    # Enhance the prompt for better cartoon results
    enhanced_prompt = _enhance_prompt(cartoon_prompt)

    # Generate a deterministic seed from the title for reproducibility
    seed = int(hashlib.md5(title.encode()).hexdigest()[:8], 16) % (2**32 - 1)
    description_for_filename = title

    # --- Try Gemini first ---
    if GEMINI_API_KEY:
        logger.info("Trying Gemini API for image generation...")
        try:
            result = _generate_with_gemini(enhanced_prompt, title, seed)
            if result:
                logger.info(f"Cartoon generated via Gemini: {result['filename']}")
                return result
            else:
                logger.warning("Gemini returned no image; falling back to Pollinations.ai")
        except Exception as e:
            logger.warning(f"Gemini generation failed ({e}); falling back to Pollinations.ai")
    else:
        logger.info("GEMINI_API_KEY not set; using Pollinations.ai directly.")

    # --- Fallback: Pollinations.ai ---
    logger.info("Using Pollinations.ai fallback...")
    for attempt in range(3):
        current_seed = seed + attempt * 1000
        encoded_prompt = quote(enhanced_prompt, safe="")
        url = f"{POLLINATIONS_BASE_URL}/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={current_seed}"

        try:
            filename = _save_image(url, description_for_filename, current_seed)
            if filename:
                logger.info(f"Cartoon generated via Pollinations: {filename}")
                return {
                    **_base_result(url, current_seed, enhanced_prompt, one_liner,
                                   comedian_angle=comedy_analysis.get("comedian_angle", ""),
                                   title=title, article_url=article_url),
                    "source": "pollinations_ai",
                }
        except Exception as e:
            logger.warning(f"Pollinations attempt {attempt + 1} failed: {e}")
            time.sleep(1)

    logger.error("All image generation attempts failed (Gemini + Pollinations).")
    return None


def _base_result(url: str, seed: int, prompt: str, one_liner: str,
                 comedian_angle: str, title: str, article_url: str) -> Dict:
    """Common result dict shared by both generators."""
    return {
        "url": url,
        "seed": seed,
        "prompt": prompt,
        "generated_at": datetime.now().isoformat(),
        "one_liner": one_liner,
        "comedian_angle": comedian_angle,
        "title": title,
        "article_url": article_url,
    }


def _generate_with_gemini(prompt: str, title: str, seed: int) -> dict[str, Any] | None:
    """Generate cartoon using Google Gemini Flash image generation API.

    Uses the native Gemini generateContent endpoint with responseModalities=["IMAGE"].
    Returns result dict with filename, or None on failure.
    """
    import json
    import base64

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
                "aspectRatio": "1:1",
                "imageSize": GEMINI_IMAGE_SIZE,
            },
        },
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        req = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(req, timeout=90) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)

        # Extract inlineData (base64 image) from response
        candidates = data.get("candidates", [])
        if not candidates:
            logger.warning("Gemini returned no candidates.")
            return None

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        for part in parts:
            inline = part.get("inlineData", {})
            if inline:
                mime_type = inline.get("mimeType", "image/png")
                b64_data = inline.get("data", "")
                if b64_data:
                    image_bytes = base64.b64decode(b64_data)
                    return _save_image_bytes(image_bytes, mime_type, title, seed)

        logger.warning("Gemini response contained no inlineData.")
        return None

    except Exception as e:
        logger.warning(f"Gemini API request failed: {e}")
        return None


def _save_image_bytes(image_data: bytes, mime_type: str, description: str, seed: int) -> dict[str, Any] | None:
    """Save image bytes directly (from Gemini base64 decode) to disk.

    Security: validates MIME type, prevents path traversal, restricts output to CARTOON_DIR.
    """
    ext = ".jpg" if "jpeg" in mime_type else ".png" if "png" in mime_type else ".jpg"

    try:
        # Validate it's actually an image using Pillow
        from PIL import Image
        from io import BytesIO

        img = Image.open(BytesIO(image_data))
        img.verify()
        # Safe to reopen after verify
        img = Image.open(BytesIO(image_data))

    except ImportError:
        logger.warning("Pillow not installed; saving raw image without validation.")
    except Exception as e:
        logger.warning(f"Pillow validation failed ({e}); rejecting image.")
        return None

    filename = build_filename(description, ext=ext)

    # Prevent path traversal
    if "/" in filename or "\\" in filename or filename.startswith("."):
        logger.warning(f"Rejected suspicious filename: {filename}")
        return None

    filepath = CARTOON_DIR / filename
    resolved = filepath.resolve()
    if not str(resolved).startswith(str(CARTOON_DIR.resolve())):
        logger.warning(f"Path traversal detected: {filepath}")
        return None

    # Handle collision
    counter = 1
    base, file_ext = filename.rsplit(".", 1)
    while filepath.exists():
        filename = f"{base}_{counter}.{file_ext}"
        filepath = CARTOON_DIR / filename
        counter += 1

    with open(filepath, "wb") as f:
        f.write(image_data)

    logger.info(f"Saved cartoon image to {filepath}")

    return {
        "filename": filename,
        "seed": seed,
        "generated_at": datetime.now().isoformat(),
        "source": "gemini",
    }


def _enhance_prompt(prompt: str) -> str:
    """Enhance the cartoon prompt for better image generation results.

    Prepends a visual style block from the style guide (art style, colors, layout).
    The incoming prompt describes the scene/narrative. Truncates to 1000 chars.
    """
    style_prefix = (
        "Warm cartoon illustration, soft watercolor-like coloring, gentle gradients, "
        "no harsh black outlines. Cute rounded character designs with big expressive eyes. "
        "Burmese people with warm light-brown/peach skin, colorful casual or work clothing. "
        "Yellow title banner at top with bold black Burmese text. "
        "Speech bubbles: white rounded ovals with thin black outlines, Burmese text inside. "
        "One animal in the scene with a completely unbothered 'don't care' expression or lazy posture. "
        "Warm beige/cream background tones (#f5e6c8), soft pastel colors throughout. "
        "Simple background with 3-5 setting-appropriate props. "
        "Artist signature in bottom-right corner. "
    )
    full = f"{style_prefix}{prompt}"
    if len(full) > 1000:
        full = full[:997] + "..."
    return full


def _save_image(url: str, description: str, seed: int) -> str | None:
    """Download and save an image from a URL.

    Used by Pollinations.ai fallback path.
    """
    if not url.startswith("https://"):
        logger.warning(f"Rejected unsafe image URL scheme: {url}")
        return None

    try:
        req = Request(url, headers={"User-Agent": "CartoonGenerator/1.0"})
        with urlopen(req, timeout=60) as response:
            image_data = response.read()

        from PIL import Image
        from io import BytesIO
        img = Image.open(BytesIO(image_data))
        img.verify()
        img = Image.open(BytesIO(image_data))

        filename = build_filename(description, ext=".jpg")
        if "/" in filename or "\\" in filename or filename.startswith("."):
            logger.warning(f"Rejected suspicious filename: {filename}")
            return None

        filepath = CARTOON_DIR / filename
        resolved = filepath.resolve()
        if not str(resolved).startswith(str(CARTOON_DIR.resolve())):
            logger.warning(f"Path traversal detected: {filepath}")
            return None

        counter = 1
        base, ext = filename.rsplit(".", 1)
        while filepath.exists():
            filename = f"{base}_{counter}.{ext}"
            filepath = CARTOON_DIR / filename
            counter += 1

        with open(filepath, "wb") as f:
            f.write(image_data)

        logger.info(f"Saved cartoon image to {filepath}")
        return filename

    except ImportError:
        logger.warning("Pillow not installed; saving raw image without validation.")
        return _save_without_validation(url, description, seed)
    except URLError as e:
        logger.warning(f"Failed to download image: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error saving image: {e}")
        return None


def _save_without_validation(url: str, description: str, seed: int) -> str | None:
    """Fallback image saving without Pillow validation."""
    if not url.startswith("https://"):
        logger.warning(f"Rejected unsafe image URL scheme: {url}")
        return None

    try:
        req = Request(url, headers={"User-Agent": "CartoonGenerator/1.0"})
        with urlopen(req, timeout=60) as response:
            image_data = response.read()

        filename = build_filename(description, ext=".jpg")
        if "/" in filename or "\\" in filename or filename.startswith("."):
            logger.warning(f"Rejected suspicious filename: {filename}")
            return None

        filepath = CARTOON_DIR / filename
        resolved = filepath.resolve()
        if not str(resolved).startswith(str(CARTOON_DIR.resolve())):
            logger.warning(f"Path traversal detected: {filepath}")
            return None

        counter = 1
        base, ext = filename.rsplit(".", 1)
        while filepath.exists():
            filename = f"{base}_{counter}.{ext}"
            filepath = CARTOON_DIR / filename
            counter += 1

        with open(filepath, "wb") as f:
            f.write(image_data)

        logger.info(f"Saved cartoon image (no validation): {filepath}")
        return filename
    except Exception as e:
        logger.warning(f"Fallback save failed: {e}")
        return None
