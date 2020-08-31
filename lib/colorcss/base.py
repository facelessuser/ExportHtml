"""Color base."""
from . import util


class _ColorBase:
    """Base color object."""

    DEF_BG = ""

    def __init__(self, color=None):
        """Initialize."""

    @property
    def a(self):
        """Alpha channel."""

        return self._c0

    @a.setter
    def a(self, value):
        """Set alpha channel."""

        self._c0 = util.clamp(value, 0.0, 1.0)

    def update_from(self, obj):
        """Update from color."""

        if self is obj:
            return

        if not isinstance(obj, type(self)):
            obj = type(self)(obj)

        self._c1 = obj._c1
        self._c2 = obj._c2
        self._c3 = obj._c3
        self.a = obj.a

    def apply_alpha(self, background=None):
        """
        Apply the given transparency with the given background.

        This gives a color that represents what the eye sees with
        the transparent color against the given background.
        """

        if background is None:
            background = type(self)(self.DEF_BG)
        elif not isinstance(background, type(self)):
            background = type(self)(background)

        if self.a < 1.0:
            self._c1 = util.mix_channel(self._c1, self.a, background._c1, background.a)
            self._c2 = util.mix_channel(self._c2, self.a, background._c2, background.a)
            self._c3 = util.mix_channel(self._c3, self.a, background._c3, background.a)
            self.a = 1.0
        return self

    def alpha(self, factor, op=util.OP_SCALE):
        """Adjust alpha."""

        if op == OP_SCALE:
            self.a = self.a + (1.0 * factor) - 1.0
        elif op == OP_ADD:
            self.a = self.a + (self.a * factor)
        elif op == OP_SUB:
            self.a = self.a - (self.a * factor)
        else:
            self.a = factor
        return self.a

    @classmethod
    def _split_channels(cls, color):
        """Split channels."""

    @classmethod
    def css_match(cls, string):
        """Match a if CSS color value."""

        return None
