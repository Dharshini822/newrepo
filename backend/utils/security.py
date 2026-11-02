import os
import re
import zipfile
from PIL import Image

def sanitize_name(name: str) -> str:
    """
    Sanitize label or folder names: alphanumeric, underscore, hyphen only.
    """
    if not name:
        return "unlabeled"
    # Replace spaces with underscores and remove any unsafe characters
    clean = re.sub(r'[^a-zA-Z0-9_\- ]', '', name.strip())
    clean = clean.replace(' ', '_').upper()
    return clean or "UNLABELED"

def is_safe_path(base_dir: str, target_path: str) -> bool:
    """
    Check that target_path resolves strictly within base_dir (prevents directory traversal / Zip Slip).
    """
    base = os.path.abspath(base_dir)
    target = os.path.abspath(target_path)
    return target.startswith(base + os.sep) or target == base

def validate_image_file(file_path: str) -> bool:
    """
    Verify that a file is a valid readable image using Pillow.
    """
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False

def safe_extract_zip(zip_path: str, extract_to: str) -> list[str]:
    """
    Safely extract a ZIP archive into extract_to directory.
    Rejects paths that escape extract_to (Zip Slip attack) and skips junk/hidden files.
    Returns list of extracted image paths.
    """
    extracted_files = []
    base_extract = os.path.abspath(extract_to)
    os.makedirs(base_extract, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            # Skip directories
            if member.is_dir():
                continue
            
            # Skip macOS metadata or hidden files
            filename = member.filename
            if "__MACOSX" in filename or os.path.basename(filename).startswith("."):
                continue

            # Check safe path
            target_path = os.path.abspath(os.path.join(base_extract, filename))
            if not is_safe_path(base_extract, target_path):
                raise ValueError(f"Unsafe file path detected in ZIP archive: {filename}")

            # Verify file extension is an image
            ext = os.path.splitext(filename)[1].lower()
            if ext not in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
                continue

            # Ensure destination folder exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Extract file
            with zf.open(member) as source, open(target_path, "wb") as target:
                target.write(source.read())

            # Validate that extracted file is a real image
            if validate_image_file(target_path):
                extracted_files.append(target_path)
            else:
                try:
                    os.remove(target_path)
                except OSError:
                    pass

    return extracted_files
