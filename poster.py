"""Post photo carousels to TikTok or save locally as fallback."""

import os
import json
import shutil
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


def post_to_tiktok(image_paths: list[str], caption: str) -> str | None:
    """Post a photo carousel to TikTok using the Content Posting API.

    TikTok Content Posting API flow:
    1. Initialize upload with photo_images source
    2. Upload each image
    3. Publish with caption

    Returns tiktok_post_id on success, None on failure.
    """
    access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
    if not access_token:
        logger.warning("No TIKTOK_ACCESS_TOKEN set — falling back to local save")
        return None

    try:
        # Step 1: Get creator info to confirm token works
        info_resp = requests.get(
            "https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
            headers={"Authorization": f"Bearer {access_token}",
                     "Content-Type": "application/json"},
            timeout=15,
        )
        if info_resp.status_code != 200:
            logger.error(f"TikTok creator info failed: {info_resp.status_code} {info_resp.text}")
            return None

        # Step 2: Initialize photo post
        init_payload = {
            "post_info": {
                "title": caption[:150],  # TikTok title limit
                "description": caption,
                "disable_comment": False,
                "privacy_level": "PUBLIC_TO_EVERYONE",
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "photo_cover_index": 0,
                "photo_images": [f"image_{i}" for i in range(len(image_paths))],
            },
            "post_mode": "DIRECT_POST",
            "media_type": "PHOTO",
        }

        init_resp = requests.post(
            "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
            headers={"Authorization": f"Bearer {access_token}",
                     "Content-Type": "application/json"},
            json=init_payload,
            timeout=15,
        )

        if init_resp.status_code != 200:
            logger.error(f"TikTok init failed: {init_resp.status_code} {init_resp.text}")
            return None

        init_data = init_resp.json().get("data", {})
        publish_id = init_data.get("publish_id")
        upload_url = init_data.get("upload_url")

        if not publish_id:
            logger.error("No publish_id returned from TikTok init")
            return None

        # Step 3: Upload images
        for i, img_path in enumerate(image_paths):
            with open(img_path, "rb") as f:
                upload_resp = requests.put(
                    upload_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "image/png",
                    },
                    data=f.read(),
                    timeout=30,
                )
                if upload_resp.status_code not in (200, 201):
                    logger.error(f"TikTok upload failed for image {i}: "
                                  f"{upload_resp.status_code}")
                    return None

        logger.info(f"TikTok post published: {publish_id}")
        return publish_id

    except Exception as e:
        logger.error(f"TikTok posting failed: {e}")
        return None


def save_locally(image_paths: list[str], caption: str, pillar: int) -> str:
    """Save carousel images and caption to output/ directory for manual upload.

    Returns the output directory path.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(__file__), "output",
                               f"{timestamp}_pillar{pillar}")
    os.makedirs(output_dir, exist_ok=True)

    # Copy images
    saved_paths = []
    for i, img_path in enumerate(image_paths):
        dest = os.path.join(output_dir, f"slide_{i + 1}.png")
        shutil.copy2(img_path, dest)
        saved_paths.append(dest)

    # Save caption
    caption_path = os.path.join(output_dir, "caption.txt")
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(caption)

    # Save metadata
    meta = {
        "pillar": pillar,
        "created_at": datetime.utcnow().isoformat(),
        "num_slides": len(image_paths),
        "image_files": [os.path.basename(p) for p in saved_paths],
    }
    meta_path = os.path.join(output_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"Carousel saved locally: {output_dir}")
    return output_dir


def post_carousel(image_paths: list[str], caption: str, pillar: int) -> tuple[str | None, str]:
    """Try TikTok API first, fall back to local save.

    Returns (tiktok_post_id_or_None, local_output_dir).
    """
    # Always save locally as a backup
    local_dir = save_locally(image_paths, caption, pillar)

    # Try TikTok API
    tiktok_id = post_to_tiktok(image_paths, caption)

    return tiktok_id, local_dir
