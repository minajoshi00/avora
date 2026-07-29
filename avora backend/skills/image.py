# ============================================================
#                       skills/image.py
#                  AI FRIEND IMAGE GENERATION
# ============================================================

import os
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from dotenv import load_dotenv
from app_paths import APP_DATA_DIR, BASE_DIR, ICON_PATH


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

try:
    _ENV_CANDIDATES = [
        APP_DATA_DIR / ".env",
        Path.cwd() / ".env",
    ]

    if getattr(sys, "_MEIPASS", None):
        _ENV_CANDIDATES.insert(0, Path(sys._MEIPASS) / ".env")

    for _env_path in _ENV_CANDIDATES:
        if _env_path.exists():
            try:
                load_dotenv(dotenv_path=_env_path, override=False)
            except Exception:
                pass
            break
except Exception:
    pass


# ============================================================
# CONFIGURATION
# ============================================================

POLLINATIONS_API_KEY = os.getenv(
    "POLLINATIONS_API_KEY"
)


# ============================================================
# PATHS
# ============================================================

IMAGE_FOLDER = APP_DATA_DIR / "generated_images"

APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# POLLINATIONS API
# ============================================================

POLLINATIONS_URL = (
    "https://image.pollinations.ai/prompt/"
)


# ============================================================
# CREATE FILE NAME
# ============================================================

def create_image_filename():

    timestamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    return IMAGE_FOLDER / (
        f"ai_image_{timestamp}.jpg"
    )


# ============================================================
# GENERATE IMAGE
# ============================================================

def generate_image(prompt):

    if not prompt:

        return {
            "type": "error",
            "message": "Brooo 😭 tell me what image you want me to generate.",
        }


    prompt = str(prompt).strip()


    if not prompt:

        return {
            "type": "error",
            "message": "Brooo 😭 please describe the image.",
        }


    try:

        print(
            "[IMAGE] Generating image..."
        )

        print(
            "[IMAGE PROMPT]",
            prompt
        )

        encoded_prompt = urllib.parse.quote(prompt)

        image_url = (
            f"{POLLINATIONS_URL}"
            f"{encoded_prompt}"
            "?width=1024"
            "&height=1024"
            "&nologo=true"
        )

        headers = {}

        if POLLINATIONS_API_KEY:
            headers["Authorization"] = f"Bearer {POLLINATIONS_API_KEY}"

        response = requests.get(
            image_url,
            headers=headers,
            timeout=180,  # 3 minute timeout for image generation
        )

        if response.status_code != 200:
            print("[IMAGE ERROR]", response.status_code, response.text[:500])
            return {
                "type": "error",
                "message": f"Brooo 😭 image generation failed. Server returned status {response.status_code}.",
            }

        content_type = response.headers.get("content-type", "")
        if not response.content:
            return {
                "type": "error",
                "message": "Brooo 😭 the image generator returned an empty image.",
            }

        if not content_type.startswith("image/"):
            text_body = response.text.strip()
            if text_body:
                print("[IMAGE] Unexpected response body:", text_body[:400])
                return {
                    "type": "error",
                    "message": "Brooo 😭 the image service returned an unexpected response.",
                }

        image_path = create_image_filename()
        suffix = ".png" if "png" in content_type else ".jpg"
        image_path = image_path.with_suffix(suffix)

        with open(image_path, "wb") as image_file:
            image_file.write(response.content)

        print("[IMAGE] Saved:", image_path)

        return {
            "type": "image",
            "path": str(image_path),
            "caption": "Here is your generated image 🎨",
        }

    except requests.exceptions.Timeout:
        return {
            "type": "error",
            "message": "Brooo 😭 image generation took too long and timed out.",
        }

    except requests.exceptions.ConnectionError:
        return {
            "type": "error",
            "message": "Brooo 😭 I couldn't connect to the image-generation service.",
        }

    except Exception as error:
        print("[IMAGE GENERATION ERROR]", error)
        return {
            "type": "error",
            "message": "Brooo 😭 something went wrong while generating the image.",
        }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "============================================"
    )

    print(
        "        AI FRIEND IMAGE GENERATOR"
    )

    print(
        "============================================"
    )

    prompt = input(
        "\nDescribe the image: "
    ).strip()


    result = generate_image(
        prompt
    )


    print(
        "\n"
        + result
    )