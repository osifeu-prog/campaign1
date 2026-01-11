from PIL import Image
import io

class ImageService:
    @staticmethod
    def resize_image(image_bytes: bytes, target_size=(640, 360)) -> io.BytesIO:
        img = Image.open(io.BytesIO(image_bytes))
        # שינוי גודל תוך שמירה על יחס (או כפייה לפי דרישתך)
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        
        bio = io.BytesIO()
        bio.name = 'image.jpeg'
        img.save(bio, 'JPEG')
        bio.seek(0)
        return bio

    @staticmethod
    def resize_gif(gif_bytes: bytes, target_size=(640, 360)) -> io.BytesIO:
        # טיפול בסיסי ב-GIF (פריים ראשון) - לעיבוד GIF מלא נדרש לופ על פריימים
        img = Image.open(io.BytesIO(gif_bytes))
        bio = io.BytesIO()
        img.save(bio, format="GIF", save_all=True) # כאן ניתן להוסיף לוגיקת שינוי גודל לכל פריים
        bio.seek(0)
        return bio
