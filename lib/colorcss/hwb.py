"""HWB class."""
from .base import _ColorBase
from . import util
import re

__all__ = ("HWB",)


class _HWB(_ColorBase):
    """HWB class."""

    DEF_BG = "hwb(0 0% 0% / 1.0)"
    CSS_MATCH = re.compile(
        r"""(?xi)
        ^hwb?\(\s*
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
    def w(self):
        """Whiteness channel."""

        return self._c2

    @w.setter
    def w(self, value):
        """Set whiteness channel."""

        self._c2 = util.clamp(value, 0.0, 1.0)

    @property
    def b(self):
        """Blackness channel."""

        return self._c3

    @b.setter
    def b(self, value):
        """Set blackness channel."""

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
            value = self._get_hwba(comma=comma)
        else:
            value = self._get_hwb(comma=comma)
        return value

    def _get_hwb(self, *, comma=False):
        """Get RGB color."""

        template = "hwb({:d}, {:d}%, {:d}%)" if comma else "hwb({:d} {:d}% {:d}%)"

        return template.format(
            util.round_int(self.h * 360.0),
            util.round_int(self.w * 100.0),
            util.round_int(self.b * 100.0)
        )

    def _get_hwba(self, *, comma=False):
        """Get RGB color with alpha channel."""

        template = "hwb({:d}, {:d}%, {:d}%, {})" if comma else "hwb({:d} {:d}% {:d}% / {})"

        return template.format(
            util.round_int(self.h * 360.0),
            util.round_int(self.w * 100.0),
            util.round_int(self.b * 100.0),
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

    def whiteness(self, factor, op=util.OP_SCALE):
        """Saturate or unsaturate the color by the given factor."""

        if op == util.OP_SCALE:
            self.w = self.w + factor - 1.0
        elif op == util.OP_ADD:
            self.w = self.w + (self.w * factor)
        elif op == util.OP_SUB:
            self.w = self.w - (self.w * factor)
        else:
            self.w = factor
        return self.w

    def blackness(self, factor, op=util.OP_SCALE):
        """Get true luminance."""

        if op == util.OP_SCALE:
            self.b = self.b + factor - 1.0
        elif op == util.OP_ADD:
            self.b = self.b + (self.b * factor)
        elif op == util.OP_SUB:
            self.b = self.b - (self.b * factor)
        else:
            self.b = factor
        return self.b

    @classmethod
    def _split_channels(cls, color):
        """Split channels."""

        start = 4
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
        else:
            None
