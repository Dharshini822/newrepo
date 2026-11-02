import os
import shutil
import uuid
import json
from PIL import Image
import config
from backend.utils.security import sanitize_name, is_safe_path, validate_image_file, safe_extract_zip

class DatasetService:
    @staticmethod
    def get_stats() -> dict:
        """
        Returns real dataset statistics based on files in dataset/train and dataset/validation.
        """
        train_dir = config.TRAIN_DIR
        val_dir = config.VAL_DIR

        train_dist = {}
        val_dist = {}
        all_classes = set()

        # Scan train directory
        if os.path.exists(train_dir):
            for cls_folder in os.listdir(train_dir):
                cls_path = os.path.join(train_dir, cls_folder)
                if os.path.isdir(cls_path):
                    clean_name = sanitize_name(cls_folder)
                    images = [f for f in os.listdir(cls_path) if os.path.splitext(f)[1].lower() in config.ALLOWED_IMAGE_EXTENSIONS]
                    train_dist[clean_name] = len(images)
                    all_classes.add(clean_name)

        # Scan validation directory
        if os.path.exists(val_dir):
            for cls_folder in os.listdir(val_dir):
                cls_path = os.path.join(val_dir, cls_folder)
                if os.path.isdir(cls_path):
                    clean_name = sanitize_name(cls_folder)
                    images = [f for f in os.listdir(cls_path) if os.path.splitext(f)[1].lower() in config.ALLOWED_IMAGE_EXTENSIONS]
                    val_dist[clean_name] = len(images)
                    all_classes.add(clean_name)

        sorted_classes = sorted(list(all_classes))
        class_stats = []
        total_train = 0
        total_val = 0

        for cls in sorted_classes:
            t_cnt = train_dist.get(cls, 0)
            v_cnt = val_dist.get(cls, 0)
            total_train += t_cnt
            total_val += v_cnt
            class_stats.append({
                "class_name": cls,
                "train_count": t_cnt,
                "val_count": v_cnt,
                "total_count": t_cnt + v_cnt
            })

        return {
            "total_images": total_train + total_val,
            "train_images": total_train,
            "val_images": total_val,
            "classes": sorted_classes,
            "num_classes": len(sorted_classes),
            "distribution": class_stats
        }

    @staticmethod
    def add_single_sample(file_storage, class_name: str, split: str = "train") -> dict:
        """
        Saves an uploaded single image to dataset/<split>/<class_name>/<unique_id>.png
        """
        clean_cls = sanitize_name(class_name)
        if split not in {"train", "validation"}:
            split = "train"

        target_dir = os.path.join(config.DATASET_DIR, split, clean_cls)
        os.makedirs(target_dir, exist_ok=True)

        ext = os.path.splitext(file_storage.filename)[1].lower()
        if ext not in config.ALLOWED_IMAGE_EXTENSIONS:
            ext = ".png"

        unique_name = f"{clean_cls}_{uuid.uuid4().hex[:8]}{ext}"
        destination = os.path.join(target_dir, unique_name)

        file_storage.save(destination)

        # Validate with PIL
        if not validate_image_file(destination):
            try:
                os.remove(destination)
            except OSError:
                pass
            raise ValueError("Uploaded file is not a valid, readable image.")

        return {
            "success": True,
            "filename": unique_name,
            "class_name": clean_cls,
            "split": split,
            "path": f"dataset/{split}/{clean_cls}/{unique_name}"
        }

    @staticmethod
    def process_zip_dataset(zip_file_path: str, default_split: str = "train") -> dict:
        """
        Safely unpacks and structures a dataset ZIP archive.
        If the zip contains class subfolders (e.g. A/image1.jpg, B/image2.jpg),
        preserves those classes into dataset/train/<class>/ and/or dataset/validation/<class>/.
        """
        temp_extract_dir = os.path.join(config.UPLOADS_DIR, f"extract_{uuid.uuid4().hex[:8]}")
        os.makedirs(temp_extract_dir, exist_ok=True)

        extracted_files = safe_extract_zip(zip_file_path, temp_extract_dir)
        total_extracted = len(extracted_files)
        organized_count = 0
        classes_added = set()

        for file_path in extracted_files:
            rel_path = os.path.relpath(file_path, temp_extract_dir)
            parts = rel_path.replace("\\", "/").split("/")

            # Check if directory structure contains train/val split and class name
            # Examples:
            # - train/A/img.jpg -> split=train, class=A
            # - A/img.jpg -> split=default_split, class=A
            # - img.jpg -> split=default_split, class=UNLABELED
            if len(parts) >= 3 and parts[0].lower() in {"train", "validation", "val", "test"}:
                split = "validation" if parts[0].lower() in {"val", "validation", "test"} else "train"
                cls_name = sanitize_name(parts[1])
            elif len(parts) >= 2:
                split = default_split
                cls_name = sanitize_name(parts[0])
            else:
                split = default_split
                cls_name = "UNLABELED"

            classes_added.add(cls_name)
            dest_dir = os.path.join(config.DATASET_DIR, split, cls_name)
            os.makedirs(dest_dir, exist_ok=True)

            unique_filename = f"{cls_name}_{uuid.uuid4().hex[:8]}_{os.path.basename(file_path)}"
            dest_file = os.path.join(dest_dir, unique_filename)
            shutil.copy2(file_path, dest_file)
            organized_count += 1

        # Clean up temporary extraction folder
        try:
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
            if os.path.exists(zip_file_path):
                os.remove(zip_file_path)
        except Exception:
            pass

        return {
            "success": True,
            "total_extracted": total_extracted,
            "organized_count": organized_count,
            "classes_detected": sorted(list(classes_added))
        }

    @staticmethod
    def list_samples(class_name: str = None, split: str = None, limit: int = 40, offset: int = 0) -> list[dict]:
        """
        Lists image samples stored in the dataset with metadata.
        """
        samples = []
        splits_to_check = [split] if split in {"train", "validation"} else ["train", "validation"]

        for s in splits_to_check:
            s_dir = os.path.join(config.DATASET_DIR, s)
            if not os.path.exists(s_dir):
                continue
            for cls_folder in os.listdir(s_dir):
                if class_name and sanitize_name(cls_folder) != sanitize_name(class_name):
                    continue
                cls_path = os.path.join(s_dir, cls_folder)
                if not os.path.isdir(cls_path):
                    continue
                for fname in os.listdir(cls_path):
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in config.ALLOWED_IMAGE_EXTENSIONS:
                        full_p = os.path.join(cls_path, fname)
                        size_kb = round(os.path.getsize(full_p) / 1024, 1)
                        samples.append({
                            "split": s,
                            "class_name": sanitize_name(cls_folder),
                            "filename": fname,
                            "relative_path": f"{s}/{cls_folder}/{fname}",
                            "size_kb": size_kb
                        })

        total_samples = len(samples)
        paginated = samples[offset:offset + limit]
        return {
            "total": total_samples,
            "samples": paginated
        }

    @staticmethod
    def delete_sample(relative_path: str) -> bool:
        """
        Deletes a sample safely within dataset/train or dataset/validation.
        """
        clean_rel = relative_path.replace("\\", "/").lstrip("/")
        target_path = os.path.abspath(os.path.join(config.DATASET_DIR, clean_rel))

        if not is_safe_path(config.DATASET_DIR, target_path):
            raise ValueError("Unsafe file path deletion attempt.")

        if os.path.exists(target_path) and os.path.isfile(target_path):
            os.remove(target_path)
            # Remove class directory if empty
            parent_dir = os.path.dirname(target_path)
            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                try:
                    os.rmdir(parent_dir)
                except OSError:
                    pass
            return True
        return False

    @staticmethod
    def generate_manifest() -> dict:
        """
        Exports a complete manifest JSON of the dataset.
        """
        stats = DatasetService.get_stats()
        manifest = {
            "project": "SignAI — Sign. Translate. Connect.",
            "version": "1.0",
            "summary": stats,
            "splits": {
                "train_dir": "dataset/train",
                "validation_dir": "dataset/validation"
            }
        }
        return manifest
