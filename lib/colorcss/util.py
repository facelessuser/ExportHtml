import re
from colorsys import rgb_to_hls, hls_to_rgb, rgb_to_hsv, hsv_to_rgb
import decimal
import sublime

HSL_WORKAROUND = int(sublime.version()) < 4069

RGB_CHANNEL_SCALE = 1.0 / 255.0
HUE_SCALE = 1.0 / 360.0
SCALE_PERCENT = 1 / 100.0

CONVERT_TURN = 360
CONVERT_GRAD = 90 / 100

CS_RGB = 0
CS_HSL = 1
CS_HWB = 2

OP_NULL = 0
OP_SCALE = 1
OP_ADD = 2
OP_SUB = 3

RE_CHAN_SPLIT = re.compile(r'(?:\s*[,/]\s*|\s+)')
RE_FLOAT_TRIM_RE = re.compile(r'^(?P<keep>\d+)(?P<trash>\.0+|(?P<keep2>\.\d*[1-9])0+)$')

COLOR_PARTS = {
    "percent": r"[+\-]?(?:(?:[0-9]*\.[0-9]+)|[0-9]+)%",
    "float": r"[+\-]?(?:(?:[0-9]*\.[0-9]+)|[0-9]+)",
    "angle": r"[+\-]?(?:(?:[0-9]*\.[0-9]+)|[0-9]+)(deg|rad|turn|grad)?",
    "space": r"\s+",
    "comma": r"\s*,\s*",
    "slash": r"\s*/\s*",
    "hex": r"[a-f0-9]"
}


def rgb_to_hsl(r, g, b):
    """RGB to HSL."""

    h, l, s = rgb_to_hls(r, g, b)
    return h, s, l

def hsl_to_rgb(h, s, l):
    """HSL to RGB."""

    return hls_to_rgb(h, l, s)


def hwb_to_rgb(h, w, b):
    """HWB to RGB."""

    # Normalize white and black
    # w + b <= 1.0
    if w + b > 1.0:
        norm_factor = 1.0 / (w + b)
        w *= norm_factor
        b *= norm_factor

    # Convert to `HSV` and then to `RGB`
    s = 1.0 - (w / (1.0 - b))
    v = 1.0 - b
    r, g, b = hsv_to_rgb(h, s, v)
    r = clamp(r, 0.0, 1.0)
    g = clamp(g, 0.0, 1.0)
    b = clamp(b, 0.0, 1.0)
    return r, g, b


def rgb_to_hwb(r, g, b):
    """RGB to HWB."""

    h, s, v = rgb_to_hsv(r, g, b)
    w = (1.0 - s) * v
    b = 1.0 - v
    return h, w, b


def hsl_to_hwb(h, s, l):
    """HSL to HWB."""

    r, g, b = hsl_to_rgb(h, s, l)
    return rgb_to_hwb(r, g, b)


def hwb_to_hsl(h, w, b):
    """HWB to HSL."""

    r, g, b = hwb_to_rgb(h, w, b)
    return rgb_to_hwb(r, g, b)


def rgb_blend_channel(c1, c2, f):
    """Blend the red, green, blue style channel."""

    return clamp(
        abs(c1 * f + c2 * (1 - f)),
        0, 1.0
    )


def percent_blend_channel(c1, c2, f):
    """Blend the percent style channel."""

    return clamp(
        abs(c1 * f + c2 * (1 - f)),
        0.0, 1.0
    )


def hue_blend_channel(c1, c2, f):
    """Blend the hue style channel."""

    c1 *= 360.0
    c2 *= 360.0

    if abs(c1 - c2) > 180.0:
        if c1 < c2:
            c1 += 360.0
        else:
            c2 += 360.0

    if HSL_WORKAROUND:
        # This shouldn't be necessary and is probably a bug in Sublime.
        f = 1.0 - f

    value = abs(c1 * f + c2 * (1 - f))
    while value > 360.0:
        value -= 360.0

    return value * HUE_SCALE


def mix_channel(cf, af, cb, ab):
    """
    Mix the color channel.

    `cf`: Channel foreground
    `af`: Alpha foreground
    `cb`: Channel background
    `ab`: Alpha background

    The foreground is overlayed on the secondary color it is to be mixed with.
    The alpha channels are applied and the colors mix.
    """

    return clamp(
        abs(
            cf * (af * 1.0) + cb * (ab * 1.0) * (1.0 - (af * 1.0))
        ),
        0, 1.0
    )


def clamp(value, mn, mx):
    """Clamp the value to the the given minimum and maximum."""

    return max(min(value, mx), mn)


def round_int(dec):
    """Round float to nearest int using expected rounding."""

    return int(decimal.Decimal(dec).quantize(decimal.Decimal('0'), decimal.ROUND_HALF_DOWN))


def fmt_float(f, p=0):
    """Set float precision and trim precision zeros."""

    string = str(
        decimal.Decimal(f).quantize(decimal.Decimal('0.' + ('0' * p) if p > 0 else '0'), decimal.ROUND_HALF_UP)
    )

    m = RE_FLOAT_TRIM.match(string)
    if m:
        string = m.group('keep')
        if m.group('keep2'):
            string += m.group('keep2')
    return string


def norm_perc_channel(value):
    """Normalize percent channel."""

    return clamp(float(value.strip('%')), 0.0, 100.0) * SCALE_PERCENT


def norm_rgb_channel(value):
    """Normailze RGB channel."""

    if value.endswith("%"):
        return norm_perc_channel(value)
    else:
        return clamp(float(value), 0.0, 255.0) * RGB_CHANNEL_SCALE


def norm_alpha_channel(value):
    """Normalize alpha channel."""

    if value.endswith("%"):
        return norm_perc_channel(value)
    else:
        return clamp(float(value), 0.0, 1.0)


def norm_hex_channel(value):
    """Normalize hex channel."""

    return int(value, 16) * RGB_CHANNEL_SCALE


def norm_angle(angle):
    """Normalize angle units."""

    if angle.endswith('turn'):
        value = float(angle[:-4]) * CONVERT_TURN
    elif angle.endswith('grad'):
        value = float(angle[:-4]) * CONVERT_GRAD
    elif angle.endswith('rad'):
        value = math.degrees(float(angle[:-3]))
    elif angle.endswith('grad'):
        value = float(angle[:-3]) * CONVERT_GRAD
    elif angle.endswith('deg'):
        value = float(angle[:-3])
    else:
        value = float(angle)
    return value


def norm_hue_channel(value):
    """Normalize hex channel."""

    return clamp(norm_angle(value), 0.0, 360.0) * HUE_SCALE
