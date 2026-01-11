from PIL import Image

def resize_image(path, size):
    img = Image.open(path)
    img = img.resize(size)
    out = path.replace(".jpg", "_out.jpg")
    img.save(out)
    return out
