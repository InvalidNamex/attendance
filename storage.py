"""
Supabase Storage helper for uploading photos to the "photos" bucket.
"""

import os
import uuid
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")  # service_role key recommended
BUCKET_NAME: str = "photos"

_client: Optional[Client] = None


def _get_client() -> Client:
    """Lazy-initialise and return the Supabase client."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY environment variables are required "
                "for storage uploads."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def upload_photo(file_bytes: bytes, original_filename: str) -> str:
    """
    Upload a photo to the Supabase "photos" bucket.

    Parameters
    ----------
    file_bytes : bytes
        Raw file content.
    original_filename : str
        The original filename (used to extract the extension).

    Returns
    -------
    str
        The public URL of the uploaded file.
    """
    ext = os.path.splitext(original_filename)[1] if original_filename else ".jpg"
    unique_name = f"{uuid.uuid4()}{ext}"

    client = _get_client()

    # Upload to bucket
    client.storage.from_(BUCKET_NAME).upload(
        path=unique_name,
        file=file_bytes,
        file_options={"content-type": _content_type(ext)},
    )

    # Build the public URL
    public_url: str = client.storage.from_(BUCKET_NAME).get_public_url(unique_name)
    return public_url


def delete_photo(photo_url: str) -> None:
    """
    Delete a photo from the Supabase "photos" bucket by its public URL.

    Silently ignores errors so a failed delete never blocks the caller.
    """
    try:
        # Extract the file name from the public URL
        # URL format: https://<project>.supabase.co/storage/v1/object/public/photos/<filename>
        filename = photo_url.rsplit("/", 1)[-1]
        if not filename:
            return
        client = _get_client()
        client.storage.from_(BUCKET_NAME).remove([filename])
    except Exception as e:
        print(f"Warning: Could not delete photo from storage: {e}")


def _content_type(ext: str) -> str:
    """Map common image extensions to MIME types."""
    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    return mapping.get(ext.lower(), "application/octet-stream")
