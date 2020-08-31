"""Color Library."""
from .rgb import _RGB
from .hsl import _HSL
from .hwb import _HWB
from . import util

__all__ = ("RGB", "HSL", "HWB", "CS_RGB", "CS_HSL", "CS_HWB", "OP_NULL", "OP_SCALE", "OP_ADD", "OP_SUB")

CS_RGB = util.CS_RGB
CS_HSL = util.CS_HSL
CS_HWB = util.CS_HWB

OP_NULL = util.OP_NULL
OP_SCALE = util.OP_SCALE
OP_ADD = util.OP_ADD
OP_SUB = util.OP_SUB


class _ColorUtil:
    """Color utility functions."""

    def get_luminance(self):
        """Get perceived luminance."""

        rgb = RGB(self)
        return util.clamp(
            util.round_int(0.299 * (rgb.r * 255.0) + 0.587 * (rgb.g * 255.0) + 0.114 * (rgb.b * 255.0)),
            0,
            255
        )

    def colorize(self, deg):
        """Colorize the color with the given hue."""

        hsl = HSL(self)
        hsl.h = deg * util.HUE_SCALE
        self.update_from(hsl)

    def contrast(self, factor):
        """Adjust contrast."""

        rgb = RGB(self)
        # Algorithm can't handle any thing beyond +/-255 (or a factor from 0 - 2)
        # Convert factor between (-255, 255)
        f = (clamp(factor, 0.0, 2.0) - 1.0) * 255.0
        f = (259 * (f + 255)) / (255 * (259 - f))

        # Increase/decrease contrast accordingly.
        rgb.r = util.clamp((f * ((rgb.r * 255.0) - 128.0)) + 128.0, 0, 255.0) * util.RGB_CHANNEL_SCALE
        rgb.g = util.clamp((f * ((rgb.g * 255.0) - 128.0)) + 128.0, 0, 255.0) * util.RGB_CHANNEL_SCALE
        rgb.b = util.clamp((f * ((rgb.b * 255.0) - 128.0)) + 128.0, 0, 255.0) * util.RGB_CHANNEL_SCALE
        self.update_from(rgb)

    def invert(self):
        """Invert the color."""

        rgb = RGB(self)
        rgb.r ^= 0xFF
        rgb.g ^= 0xFF
        rgb.b ^= 0xFF
        self.update_from(rgb)

    def grayscale(self):
        """Convert the color with a grayscale filter."""

        rgb = RGB(self)
        luminance = self.get_luminance()
        rgb.r = luminance
        rgb.g = luminance
        rgb.b = luminance
        self.update_from(rgb)

    def sepia(self):
        """Apply a sepia filter to the color."""

        rgb = RGB(self)
        rgb.r = (rgb.r * .393) + (rgb.g * .769) + (rgb.b * .189)
        rgb.g = (rgb.r * .349) + (rgb.g * .686) + (rgb.b * .168)
        rgb.b = (rgb.r * .272) + (rgb.g * .534) + (rgb.b * .131)
        self.update_from(rgb)

    def _get_overage(self, c):
        """Get overage."""

        if c < 0.0:
            o = 0.0 + c
            c = 0.0
        elif c > 255.0:
            o = c - 255.0
            c = 255.0
        else:
            o = 0.0
        return o, c

    def _distribute_overage(self, c, o, s):
        """Distribute overage."""

        channels = len(s)
        if channels == 0:
            return c
        parts = o / len(s)
        if "r" in s and "g" in s:
            c = c[0] + parts, c[1] + parts, c[2]
        elif "r" in s and "b" in s:
            c = c[0] + parts, c[1], c[2] + parts
        elif "g" in s and "b" in s:
            c = c[0], c[1] + parts, c[2] + parts
        elif "r" in s:
            c = c[0] + parts, c[1], c[2]
        elif "g" in s:
            c = c[0], c[1] + parts, c[2]
        else:  # "b" in s:
            c = c[0], c[1], c[2] + parts
        return c

    def brightness(self, factor):
        """
        Adjust the brightness by the given factor.

        Brightness is determined by perceived luminance.
        """

        rgb = RGB(self)
        channels = ["r", "g", "b"]
        total_lumes = clamp(rgb.get_luminance() + (1.0 * factor) - 1.0, 0.0, 1.0)

        if total_lumes == 1.0:
            # white
            rgb.r, rgb.g, rgb.b = 1.0, 1.0, 1.0
        elif total_lumes == 0.0:
            # black
            rgb.r, rgb.g, rgb.b = 0.0, 0.0, 0.0
        else:
            # Adjust Brightness
            pts = (total_lumes - 0.299 * rgb.r - 0.587 * rgb.g - 0.114 * rgb.b)
            slots = set(channels)
            components = [float(rgb.r) + pts, float(rgb.g) + pts, float(rgb.b) + pts]
            count = 0
            for c in channels:
                overage, components[count] = self._get_overage(components[count])
                if overage:
                    slots.remove(c)
                    components = list(self._distribute_overage(components, overage, slots))
                count += 1

            rgb.r = components[0]
            rgb.g = components[1]
            rgb.b = components[2]
        self.update_from(rgb)

    def blend(self, color, percent, alpha=False, color_space=CS_RGB):
        """Blend color."""

        factor = util.clamp(util.clamp(float(percent), 0.0, 100.0) * SCALE_PERCENT, 0.0, 1.0)

        if color_space == CS_RGB:
            if not isinstance(color, RGB):
                color = RGB(color)
            this = RGB(self) if not isinstance(self, RGB) else self
            this.r = util.rgb_blend_channel(this.r, color.r, factor)
            this.g = util.rgb_blend_channel(this.g, color.g, factor)
            this.b = util.rgb_blend_channel(this.b, color.b, factor)
        elif color_space == CS_HSL:
            if not isinstance(color, HSL):
                color = HSL(color)
            this = HSL(self) if not isinstance(self, HSL) else self
            this.h = util.hue_blend_channel(this.h, color.h, factor)
            this.l = util.percent_blend_channel(this.l, color.l, factor)
            this.s = util.percent_blend_channel(this.s, color.s, factor)
        elif color_space == CS_HWB:
            if not isinstance(color, HWB):
                color = HSL(color)
            this = HWB(self) if not isinstance(self, HWB) else self
            this.h = util.hue_blend_channel(this.h, color.h, factor)
            this.w = util.percent_blend_channel(this.w, color.w, factor)
            this.b = util.percent_blend_channel(this.b, color.b, factor)
        else:
            raise ValueError('Invalid color space value: {}'.format(str(color_space)))

        if alpha:
            this.a = util.rgb_blend_channel(this.a, color.a, factor)
        self.update_from(this)


class RGB(_ColorUtil, _RGB):
    """RGB color class."""

    def __init__(self, color=None):
        """Initialize."""

        if isinstance(color, RGB):
            self.r, self.g, self.b, self.a = color.r, color.g, color.b, color.a
        elif isinstance(color, HSL):
            self.r, self.g, self.b = util.hsl_to_rgb(color.h, color.s, color.l)
            self.a = color.a
        elif isinstance(color, HWB):
            self.r, self.g, self.b = util.hwb_to_rgb(color.h, color.w, color.b)
            self.a = color.a
        elif isinstance(color, str):
            if color is None:
                color = self.DEF_BG
            values = self.css_match(color)
            if values is None:
                raise ValueError("'{}' does not appear to be a valid color".format(color))
            self.r, self.g, self.b, self.a = values
        elif isinstance(color, (list, tuple)):
            if not (3 <= len(color) <=4):
                raise ValueError("A list of channel values should be of length 3 or 4.")
            self.r = util.clamp(color[0], 0.0, 1.0)
            self.g = util.clamp(color[1], 0.0, 1.0)
            self.b = util.clamp(color[2], 0.0, 1.0)
            self.a = 1.0 if len(color) == 3 else util.clamp(color[3], 0.0, 1.0)
        else:
            raise TypeError("Unexpected type '{}' received".format(type(color)))


class HSL(_ColorUtil, _HSL):
    """HSL color class."""

    def __init__(self, color=None):
        """Initialize."""

        if isinstance(color, HSL):
            self.h, self.s, self.l, self.a = color.h, color.s, color.l, color.a
        elif isinstance(color, RGB):
            self.h, self.s, self.l = util.rgb_to_hsl(color.r, color.g, color.b)
            self.a = color.a
        elif isinstance(color, HWB):
            self.h, self.s, self.l = util.hwb_to_hsl(color.h, color.w, color.b)
            self.a = color.a
        elif isinstance(color, str):
            if color is None:
                color = self.DEF_BG
            values = self.css_match(color)
            if values is None:
                raise ValueError("'{}' does not appear to be a valid color".format(color))
            self.h, self.s, self.l, self.a = values
        elif isinstance(color, (list, tuple)):
            if not (3 <= len(color) <=4):
                raise ValueError("A list of channel values should be of length 3 or 4.")
            self.h = util.clamp(color[0], 0.0, 1.0)
            self.s = util.clamp(color[1], 0.0, 1.0)
            self.l = util.clamp(color[2], 0.0, 1.0)
            self.a = 1.0 if len(color) == 3 else util.clamp(color[3], 0.0, 1.0)
        else:
            raise TypeError("Unexpected type '{}' received".format(type(color)))


class HWB(_ColorUtil, _HWB):
    """HWB color class."""

    def __init__(self, color=None):
        """Initialize."""

        if isinstance(color, HWB):
            self.h, self.w, self.b, self.a = color.h, color.w, color.b, color.a
        elif isinstance(color, RGB):
            self.h, self.w, self.b = util.rgb_to_hwb(color.r, color.g, color.b)
            self.a = color.a
        elif isinstance(color, HSL):
            self.h, self.w, self.b = util.hsl_to_hwb(color.h, color.s, color.l)
            self.a = color.a
        elif isinstance(color, str):
            if color is None:
                color = self.DEF_BG
            values = self.css_match(color)
            if values is None:
                raise ValueError("'{}' does not appear to be a valid color".format(color))
            self.h, self.w, self.b, self.a = values
        elif isinstance(color, (list, tuple)):
            if not (3 <= len(color) <=4):
                raise ValueError("A list of channel values should be of length 3 or 4.")
            self.h = util.clamp(color[0], 0.0, 1.0)
            self.w = util.clamp(color[1], 0.0, 1.0)
            self.b = util.clamp(color[2], 0.0, 1.0)
            self.a = 1.0 if len(color) == 3 else util.clamp(color[3], 0.0, 1.0)
        else:
            raise TypeError("Unexpected type '{}' received".format(type(color)))


def css_color(string):
    """Parse a CSS color."""

    for colorspace in (RGB, HSL, HWB):
        value = colorspace.css_match(string)
        if value is not None:
            return colorspace(value)
    raise ValueError("'{}' doesn't appear to be a valid and/or supported CSS color".format(string))
