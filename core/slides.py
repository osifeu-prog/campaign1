import os

SLIDES_PATH = "media/start_slides"

SLIDES = [
    {
        "image": "slide1.jpg",
        "text": "👋 ברוכים הבאים לבוט הקמפיין"
    },
    {
        "image": "slide2.jpg",
        "text": "📊 הרשמה, מומחים וניהול תוכן"
    },
    {
        "image": "slide3.jpg",
        "text": "🖼 עריכת תמונות למורשים בלבד"
    }
]

def get_slide(index: int):
    slide = SLIDES[index]
    return (
        os.path.join(SLIDES_PATH, slide["image"]),
        slide["text"]
    )

def slides_count():
    return len(SLIDES)
