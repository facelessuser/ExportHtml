"""HSL class."""
from .base import _ColorBase
from . import util
import re

__all__ = ("HSL",)


class _HSL(_ColorBase):
    """HSL class."""

    DEF_BG = "hsl(0 0% 0% / 1.0)"
    CSS_MATCH = re.compile(
        r"""(?xi)
        ^hsla?\(\s*
        (?:
            # Space separated format
            {angle}{space}{percent}{space}{percent}(?:{slash}(?:{percent}|{float}))? |
            # comma separated format
            {angle}{comma}{percent}{comma}{percent}(?:{comma}(?:{percent}|{float}))?
        )
        \s*\)$
        """.format(**util.COLOR_PARTS)
    )

    @property
    def h(self):
        """Hue channel."""

        return self._c1

    @h.setter
    def h(self, value):
        """Set hue channel."""

        self._c1 = util.clamp(value, 0.0, 1.0)

    @property
    def s(self):
        """Saturation channel."""

        return self._c2

    @s.setter
    def s(self, value):
        """Set saturation channel."""

        self._c2 = util.clamp(value, 0.0, 1.0)

    @property
    def l(self):
        """Lightness channel."""

        return self._c3

    @l.setter
    def l(self, value):
        """Set lightness channel."""

        self._c3 = util.clamp(value, 0.0, 1.0)

    def __str__(self):
        """String."""

        return self.to_css(alpha=True, prefer_alpha=True)

    def to_css(
        self, *, alpha=False, prefer_alpha=False, comma=False
    ):
        """Convert to CSS."""

        value = ''
        if alpha and (prefer_alpha or self.a < 1.0):
            value = self._get_hsla(comma=comma)
        else:
            value = self._get_hsl(comma=comma)
        return value

    def _get_hsl(self, *, comma=False):
        """Get RGB color."""

        template = "hsl({:d}, {:d}%, {:d}%)" if comma else "hsl({:d} {:d}% {:d}%)"

        return template.format(
            util.round_int(self.h * 360.0),
            util.round_int(self.s * 100.0),
            util.round_int(self.l * 100.0)
        )

    def _get_hsla(self, *, comma=False):
        """Get RGB color with alpha channel."""

        template = "hsla({:d}, {:d}%, {:d}%, {})" if comma else "hsl({:d} {:d}% {:d}% / {})"

        return template.format(
            util.round_int(self.h * 360.0),
            util.round_int(self.s * 100.0),
            util.round_int(self.l * 100.0),
            util.fmt_float(self.a, 3)
        )

    def hue(self, deg):
        """Shift the hue."""

        d = deg * util.HUE_SCALE
        h = self.h + d
        while h > 1.0:
            h -= 1.0
        while h < 0.0:
            h += 1.0
        self.h = h
        return h

    def saturation(self, factor, op=util.OP_SCALE):
        """Saturate or unsaturate the color by the given factor."""

        if op == util.OP_SCALE:
            self.s = self.s + factor - 1.0
        elif op == util.OP_ADD:
            self.s = self.s + (self.s * factor)
        elif op == util.OP_SUB:
            self.s = self.s - (self.s * factor)
        else:
            self.s = factor
        return self.s

    def lightness(self, factor, op=util.OP_SCALE):
        """Get true luminance."""

        if op == util.OP_SCALE:
            self.l = self.l + factor - 1.0
        elif op == util.OP_ADD:
            self.l = self.l + (self.l * factor)
        elif op == util.OP_SUB:
            self.l = self.l - (self.l * factor)
        else:
            self.l = factor
        return self.l

    @classmethod
    def _split_channels(cls, color):
        """Split channels."""

        start = 5 if color.startswith('hsla') else 4
        channels = []
        for i, c in enumerate(util.RE_CHAN_SPLIT.split(color[start:-1].strip()), 0):
            if i == 0:
                channels.append(util.norm_hue_channel(c))
            elif i == 3:
                channels.append(util.norm_alpha_channel(c))
            else:
                channels.append(util.norm_perc_channel(c))
        if len(channels) == 3:
            channels.append(1.0)
        return channels

    @classmethod
    def css_match(cls, string):
        """Match a CSS color string."""

        if cls.CSS_MATCH.match(string) is not None:
            return cls._split_channels(string)
        return None
