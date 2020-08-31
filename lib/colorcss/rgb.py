"""RGB color class."""
from .base import _ColorBase
from . import util
from . import css_names
import re

__all__ = ("RGB",)

RE_COMPRESS = re.compile(r'(?i)^#({hex})\1({hex})\2({hex})\3(?:({hex})\4)?$')


class _RGB(_ColorBase):
    """RGB class."""

    DEF_BG = "rgb(0 0 0 / 1)"
    CSS_MATCH = re.compile(
        r"""(?xi)
        ^(?:
            # RGB syntax
            rgba?\(\s*
            (?:
                # Space separated format
                (?:
                    # Float form
                    (?:{float}{space}){{2}}{float} |
                    # Percent form
                    (?:{percent}{space}){{2}}{percent}
                )({slash}(?:{percent}|{float}))? |
                # Comma separated format
                (?:
                    # Float form
                    (?:{float}{comma}){{2}}{float} |
                    # Percent form
                    (?:{percent}{comma}){{2}}{percent}
                )({comma}(?:{percent}|{float}))?
            )
            \s*\) |
            # Hex syntax
            \#(?:{hex}{{6}}(?:{hex}{{2}})?|{hex}{{3}}(?:{hex})?)
        )$
        """.format(**util.COLOR_PARTS)
    )

    HEX_MATCH = re.compile(r"(?i)#(?:{hex}{{6}}(?:{hex}{{2}})?|{hex}{{3}}(?:{hex})?)".format(**util.COLOR_PARTS))

    @property
    def r(self):
        """Red channel."""

        return self._c1

    @r.setter
    def r(self, value):
        """Set red channel."""

        self._c1 = util.clamp(value, 0.0, 1.0)

    @property
    def g(self):
        """Green channel."""

        return self._c2

    @g.setter
    def g(self, value):
        """Set green channel."""

        self._c2 = util.clamp(value, 0.0, 1.0)

    @property
    def b(self):
        """Blue channel."""

        return self._c3

    @b.setter
    def b(self, value):
        """Set blue channel."""

        self._c3 = util.clamp(value, 0.0, 1.0)

    def __str__(self):
        """String."""

        return self.to_css(alpha=True, prefer_alpha=True)

    def to_css(
        self, *, alpha=False, prefer_alpha=False, prefer_name=False, prefer_hex=False, compress=False, comma=False
    ):
        """Convert to CSS."""

        value = ''
        if prefer_hex or prefer_name:
            h = self._get_hexa() if alpha and (prefer_alpha or self.a < 1.0) else self._get_hex()
            if prefer_hex:
                value = h
            if prefer_name:
                name = css_names.hex2name(h)
                if name is not None:
                    value = name
        if not value:
            if alpha and (prefer_alpha or self.a < 1.0):
                value = self._get_rgba(comma=comma)
            else:
                value = self._get_rgb(comma=comma)
        return value

    def _get_rgb(self, *, comma=False):
        """Get RGB color."""

        template = "rgb({:d}, {:d}, {:d})" if comma else "rgb({:d} {:d} {:d})"

        return template.format(
            util.round_int(self.r * 255.0),
            util.round_int(self.g * 255.0),
            util.round_int(self.b * 255.0)
        )

    def _get_rgba(self, *, comma=False):
        """Get RGB color with alpha channel."""

        template = "rgba({:d}, {:d}, {:d}, {})" if comma else "rgb({:d} {:d} {:d} / {})"

        return template.format(
            util.round_int(self.r * 255.0),
            util.round_int(self.g * 255.0),
            util.round_int(self.b * 255.0),
            util.fmt_float(self.a, 3)
        )

    def _get_hexa(self, *, compress=False):
        """Get the RGB color with the alpha channel."""

        value = "#{:02X}{:02X}{:02X}{:02X}".format(
            util.round_int(self.r * 255.0),
            util.round_int(self.g * 255.0),
            util.round_int(self.b * 255.0),
            util.round_int(self.a * 255.0)
        )

        if compress:
            m = RE_COMPRESS.match(value)
            if m:
                value = m.expand(r"#\1\2\3\4")
        return value

    def _get_hex(self, *, compress=False):
        """Get the `RGB` value."""

        value = "#{:02X}{:02X}{:02X}".format(
            util.round_int(self.r * 255.0),
            util.round_int(self.g * 255.0),
            util.round_int(self.b * 255.0)
        )

        if compress:
            m = RE_COMPRESS.match(value)
            if m:
                value = m.expand(r"#\1\2\3")
        return value

    def red(self, factor, op=util.OP_SCALE):
        """Adjust red."""

        if op == util.OP_SCALE:
            self.r = self.r + (1.0 * factor) - 1.0
        elif op == util.OP_ADD:
            self.r = self.r + (self.r * factor)
        elif op == util.OP_SUB:
            self.r = self.r - (self.r * factor)
        else:
            self.r = factor
        return self.r

    def green(self, factor, op=util.OP_SCALE):
        """Adjust green."""

        if op == util.OP_SCALE:
            self.g = self.g + (1.0 * factor) - 1.0
        elif op == util.OP_ADD:
            self.g = self.g + (self.g * factor)
        elif op == util.OP_SUB:
            self.g = self.g - (self.g * factor)
        else:
            self.g = factor
        return self.g

    def blue(self, factor, op=util.OP_SCALE):
        """Adjust blue."""

        if op == util.OP_SCALE:
            self.b = self.b + (1.0 * factor) - 1.0
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

        if color.startswith('rgb'):
            start = 5 if color.startswith('rgba') else 4
            channels = []
            for i, c in enumerate(util.RE_CHAN_SPLIT.split(color[start:-1].strip()), 0):
                channels.append(util.norm_alpha_channel(c) if i == 3 else util.norm_rgb_channel(c))
            if len(channels) == 3:
                channels.append(1.0)
            return channels
        else:
            m = cls.HEX_MATCH.match(color)
            assert(m is not None)
            if m.group(1):
                return (
                    int(color[1:3], 16) * util.RGB_CHANNEL_SCALE,
                    int(color[3:5], 16) * util.RGB_CHANNEL_SCALE,
                    int(color[5:7], 16) * util.RGB_CHANNEL_SCALE,
                    int(m.group(2), 16) * util.RGB_CHANNEL_SCALE if m.group(2) else 1.0
                )
            else:
                return (
                    int(color[1] * 2, 16) * util.RGB_CHANNEL_SCALE,
                    int(color[2] * 2, 16) * util.RGB_CHANNEL_SCALE,
                    int(color[3] * 2, 16) * util.RGB_CHANNEL_SCALE,
                    int(m.group(4), 16) * util.RGB_CHANNEL_SCALE if m.group(r) else 1.0
                )

    @classmethod
    def css_match(cls, string):
        """Match a CSS color string."""

        if cls.CSS_MATCH.match(string) is not None:
            return cls._split_channels(string)
        else:
            string = css_names.name2hex(string)
            if string is not None:
                return cls._split_channels(string)
        return None
