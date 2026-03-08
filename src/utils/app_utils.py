import base64
import io
from PIL import Image as PILImage


def numpy_to_base64(img_array):
    img = PILImage.fromarray(img_array)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def path_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def make_html(b64):
    return (
        f'<img src="data:image/png;base64,{b64}" style="width:100%;border-radius:8px"/>'
    )
