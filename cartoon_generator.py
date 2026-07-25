"""Generates funny cartoon images using free APIs."""
import hashlib
import logging
import random
import time
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

from config import CARTOON_DIR, POLLINATIONS_BASE_URL, build_filename

logger = logging.getLogger(__name__)


def generate_cartoon(comedy_analysis: dict) -> dict | None:
    """Generate a funny cartoon image from the comedy analysis.

    Uses Pollinations.ai (free, no API key required).
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

    # Use the article title as the description for filename
    description_for_filename = title

    # Try multiple seeds if the first doesn't produce a good result
    for attempt in range(3):
        current_seed = seed + attempt * 1000
        url = POLLINATIONS_BASE_URL.format(prompt=enhanced_prompt, seed=current_seed)

        try:
            filename = _save_image(url, description_for_filename, current_seed)
            if filename:
                logger.info(f"Cartoon generated: {filename}")
                return {
                    "filename": filename,
                    "url": url,
                    "seed": current_seed,
                    "prompt": enhanced_prompt,
                    "generated_at": datetime.now().isoformat(),
                    "one_liner": one_liner,
                    "comedian_angle": comedy_analysis.get("comedian_angle", ""),
                    "title": title,
                    "article_url": article_url,
                }
        except Exception as e:
            logger.warning(f"Image generation attempt {attempt + 1} failed: {e}")
            time.sleep(1)

    logger.error("All image generation attempts failed.")
    return None


def _enhance_prompt(prompt: str) -> str:
    """Enhance the cartoon prompt for better image generation results."""
    enhancements = [
        "funny cartoon illustration, vibrant colors, exaggerated expressions,",
        "satirical editorial cartoon style, bold lines, humorous,",
        "webcomic art style, colorful, witty visual humor,",
        "caricature illustration, comical proportions, funny,",
        "editorial cartoon, black and white with selective color, satirical,",
    ]
    enhancement = enhancements[random.randint(0, len(enhancements) - 1)]
    return f"{enhancement} {prompt}"


def _save_image(url: str, description: str, seed: int) -> str | None:
    """Download and save the generated image with configurable filename format.

    Args:
        url: The image generation URL.
        description: Short description used in the filename.
        seed: Random seed used for generation.

    Returns:
        The saved filename (relative to CARTOON_DIR), or None on failure.
    """
    try:
        req = Request(url, headers={"User-Agent": "CartoonGenerator/1.0"})
        with urlopen(req, timeout=60) as response:
            image_data = response.read()

        # Validate it's actually an image
        from PIL import Image
        from io import BytesIO

        img = Image.open(BytesIO(image_data))
        img.verify()  # This checks if it's a valid image

        # Safe to reopen after verify
        img = Image.open(BytesIO(image_data))

        # Build filename using the configured format
        filename = build_filename(description, ext=".jpg")
        filepath = CARTOON_DIR / filename

        # Handle collision: if file already exists, append a counter
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
    try:
        req = Request(url, headers={"User-Agent": "CartoonGenerator/1.0"})
        with urlopen(req, timeout=60) as response:
            image_data = response.read()

        # Build filename using the configured format
        filename = build_filename(description, ext=".jpg")
        filepath = CARTOON_DIR / filename

        # Handle collision
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
