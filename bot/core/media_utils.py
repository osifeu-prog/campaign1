# bot/core/media_utils.py
import os
import tempfile
from PIL import Image, ImageSequence
import imageio
import shutil

from typing import List, Tuple

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def resize_image(input_path: str, output_dir: str, sizes: List[Tuple[int,int]]) -> List[str]:
    """
    Resize static image to multiple sizes. Returns list of output file paths.
    """
    ensure_dir(output_dir)
    out_paths = []
    with Image.open(input_path) as im:
        for w,h in sizes:
            # maintain aspect ratio: fit into box (w,h)
            im_copy = im.copy()
            im_copy.thumbnail((w,h), Image.LANCZOS)
            base = os.path.basename(input_path)
            name, ext = os.path.splitext(base)
            out_name = f"{name}_{w}x{h}{ext}"
            out_path = os.path.join(output_dir, out_name)
            im_copy.save(out_path, optimize=True, quality=85)
            out_paths.append(out_path)
    return out_paths

def resize_gif(input_path: str, output_dir: str, sizes: List[Tuple[int,int]], max_frames: int = 200) -> List[str]:
    """
    Resize animated GIF (or video-like animation) to multiple sizes.
    Returns list of output file paths.
    """
    ensure_dir(output_dir)
    out_paths = []
    try:
        reader = imageio.get_reader(input_path)
        meta = reader.get_meta_data()
        fps = meta.get("fps", 10)
        frames = []
        for i, frame in enumerate(reader):
            frames.append(frame)
            if len(frames) >= max_frames:
                break
        reader.close()
    except Exception:
        # fallback: use PIL
        frames = []
        with Image.open(input_path) as im:
            for frame in ImageSequence.Iterator(im):
                frames.append(frame.convert("RGBA"))

    for w,h in sizes:
        out_name = os.path.splitext(os.path.basename(input_path))[0] + f"_{w}x{h}.gif"
        out_path = os.path.join(output_dir, out_name)
        # resize frames
        resized = []
        for fr in frames:
            img = Image.fromarray(fr) if not isinstance(fr, Image.Image) else fr
            img = img.convert("RGBA")
            img.thumbnail((w,h), Image.LANCZOS)
            resized.append(img)
        # save as gif
        resized[0].save(out_path, save_all=True, append_images=resized[1:], loop=0, duration=int(1000/fps))
        out_paths.append(out_path)
    return out_paths

def cleanup_files(paths: List[str]):
    for p in paths:
        try:
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
