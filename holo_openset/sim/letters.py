"""The objects of the simulated samples: letters A-Z rendered as binary masks."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CLASSES = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
FONT_DIR = Path(__file__).resolve().parent / 'fonts'
FONTS = sorted((FONT_DIR / 'main').glob('*.ttf'))      # every scene
AUX_FONTS = sorted((FONT_DIR / 'aux').glob('*.ttf'))   # auxiliary training scenes only


def clipped_normal_int(rng, mean, std, low, high):
    return max(low, min(high, int(round(rng.gauss(mean, std)))))


def letter_mask(letter, font_path, font_size, angle):
    """The letter in a font, at a size (px) and rotation (degrees) -> greyscale PIL image cropped to the ink."""
    font = ImageFont.truetype(str(font_path), font_size)
    probe = ImageDraw.Draw(Image.new('L', (font_size * 3, font_size * 3), 0))
    bbox = probe.textbbox((0, 0), letter, font=font)
    mask = Image.new('L', (bbox[2] - bbox[0] + 12, bbox[3] - bbox[1] + 12), 0)
    ImageDraw.Draw(mask).text((6 - bbox[0], 6 - bbox[1]), letter, fill=255, font=font)
    mask = mask.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    ink = mask.getbbox()
    return mask.crop(ink) if ink else mask


def write_yolo_label(path, rows, width, height):
    """One line per box: class x_centre y_centre width height (relative to the image)."""
    with open(path, 'w') as f:
        for r in rows:
            f.write(f"{r['class_id']} {(r['x0'] + r['x1']) / 2 / width:.6f} {(r['y0'] + r['y1']) / 2 / height:.6f} "
                    f"{(r['x1'] - r['x0']) / width:.6f} {(r['y1'] - r['y0']) / height:.6f}\n")
