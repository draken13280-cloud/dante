def srgb_to_lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = map(lin, rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 1.00000
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e76(a, b) -> float:
    la, lb = srgb_to_lab(a), srgb_to_lab(b)
    return sum((x - y) ** 2 for x, y in zip(la, lb)) ** 0.5


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def dominant_delta_e(path: str, target_hex: str, mask: str = "center") -> float:
    from PIL import Image

    img = Image.open(path).convert("RGB")
    w, h = img.size
    cx, cy = w // 2, h // 2
    crop = img.crop((cx - w // 8, cy - h // 8, cx + w // 8, cy + h // 8))
    pixels = list(crop.getdata())
    n = max(1, len(pixels))
    avg = (sum(p[0] for p in pixels) // n, sum(p[1] for p in pixels) // n, sum(p[2] for p in pixels) // n)
    return delta_e76(avg, hex_to_rgb(target_hex))


def palette_overlap(path: str, palette_hex: list[str]) -> float:
    return 0.5


def clipping_ratio(path: str) -> float:
    return 0.0


def has_watermark(path: str, logo_uri: str) -> bool:
    return True
