"""
Color Scheme Tweaker (for sublime text).

Licensed under MIT
Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
from __future__ import absolute_import
import sublime
from .st_colormod import Color
from coloraide import util
import re

NEW_SCHEMES = int(sublime.version()) >= 3150
FONT_STYLE = "font_style" if int(sublime.version()) >= 3151 else "fontStyle"
GLOBAL_OPTIONS = "globals" if int(sublime.version()) >= 3152 else "defaults"

FILTER_MATCH = re.compile(
    r'''(?x)
    ^(?:
        (brightness|saturation|hue|contrast|colorize|glow)\((-?[\d]+|[\d]*\.[\d]+)\)|
        (sepia|grayscale|invert)
    )
    (?:@(fg|bg))?$
    '''
)

RE_SNAKE_CASE = re.compile('_(.)')


def to_camel(m):
    """Convert to camel case."""

    return m.group(1).Upper()


def get_tmtheme(scheme):
    """Get old tmtheme style."""

    tmtheme = {
        "settings": [
            {
                "settings": {}
            }
        ]
    }

    for k, v in scheme.get(GLOBAL_OPTIONS, {}).items():
        tmtheme["settings"]["settings"][RE_SNAKE_CASE.sub(to_camel, k)] = v

    for k, v in scheme.items():
        if k in ('variables', 'rules', GLOBAL_OPTIONS):
            continue
        tmtheme[k] = v

    for rule in scheme["rules"]:
        entry = {}
        name = rule.get('name')
        scope = rule.get('scope')
        if name:
            entry['name'] = name
        if scope:
            entry['scope'] = scope

        entry['settings'] = {}

        foreground = rule.get('foreground')
        background = rule.get('background')
        fontstyle = rule.get(FONT_STYLE)
        selection_foreground = rule.get('selection_foreground')

        if foreground and isinstance(foreground, str):
            entry['settings']['foreground'] = foreground
        if selection_foreground:
            entry['selectionForeground'] = selection_foreground
        if background:
            entry['settings']['background'] = background
        if fontstyle:
            entry['settings']['fontStyle'] = fontstyle

        tmtheme['settings'].append(entry)

    return tmtheme


class _Filters:
    """Color filters."""

    @staticmethod
    def colorize(color, deg):
        """Colorize the color with the given hue."""

        if color.is_nan('hsl.hue'):
            return
        color.set('hsl.hue', deg % 360)

    @staticmethod
    def hue(color, deg):
        """Shift the hue."""

        if color.is_nan('hsl.hue'):
            return
        h = color.get('hsl.hue')
        h += deg
        h = color.set('hsl.hue', h % 360)

    @staticmethod
    def contrast(color, factor):
        """Adjust contrast."""

        r, g, b = [util.round_half_up(util.clamp(c * 255, 0, 255)) for c in util.no_nan(color.coords())]
        # Algorithm can't handle any thing beyond +/-255 (or a factor from 0 - 2)
        # Convert factor between (-255, 255)
        f = (util.clamp(factor, 0.0, 2.0) - 1.0) * 255.0
        f = (259 * (f + 255)) / (255 * (259 - f))

        # Increase/decrease contrast accordingly.
        r = util.clamp(util.round_half_up((f * (r - 128)) + 128), 0, 255)
        g = util.clamp(util.round_half_up((f * (g - 128)) + 128), 0, 255)
        b = util.clamp(util.round_half_up((f * (b - 128)) + 128), 0, 255)
        color.red = r / 255
        color.green = g / 255
        color.blue = b / 255

    @staticmethod
    def invert(color):
        """Invert the color."""

        r, g, b = [int(util.round_half_up(util.clamp(c * 255, 0, 255))) for c in util.no_nan(color.coords())]
        r ^= 0xFF
        g ^= 0xFF
        b ^= 0xFF
        color.red = r / 255
        color.green = g / 255
        color.blue = b / 255

    @staticmethod
    def saturation(color, factor):
        """Saturate or unsaturate the color by the given factor."""

        s = util.no_nan(color.get('hsl.saturation')) / 100.0
        s = util.clamp(s + factor - 1.0, 0.0, 1.0)
        color.set('hsl.saturation', s * 100)

    @staticmethod
    def grayscale(color):
        """Convert the color with a grayscale filter."""

        luminance = color.luminance()
        color.red = luminance
        color.green = luminance
        color.blue = luminance

    @staticmethod
    def sepia(color):
        """Apply a sepia filter to the color."""

        red, green, blue = util.no_nan(color.coords())
        r = util.clamp((red * .393) + (green * .769) + (blue * .189), 0, 1)
        g = util.clamp((red * .349) + (green * .686) + (blue * .168), 0, 1)
        b = util.clamp((red * .272) + (green * .534) + (blue * .131), 0, 1)
        color.red = r
        color.green = g
        color.blue = b

    @staticmethod
    def _get_overage(c):
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

    @staticmethod
    def _distribute_overage(c, o, s):
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

    @classmethod
    def brightness(cls, color, factor):
        """
        Adjust the brightness by the given factor.

        Brightness is determined by perceived luminance.
        """

        red, green, blue = [util.round_half_up(util.clamp(c * 255, 0, 255)) for c in util.no_nan(color.coords())]
        channels = ["r", "g", "b"]
        total_lumes = util.clamp(util.clamp(color.luminance(), 0, 1) * 255 + (255.0 * factor) - 255.0, 0.0, 255.0)

        if total_lumes == 255.0:
            # white
            r, g, b = 1, 1, 1
        elif total_lumes == 0.0:
            # black
            r, g, b = 0, 0, 0
        else:
            # Adjust Brightness
            pts = (total_lumes - util.clamp(color.luminance(), 0, 1) * 255)
            slots = set(channels)
            components = [float(red) + pts, float(green) + pts, float(blue) + pts]
            count = 0
            for c in channels:
                overage, components[count] = cls._get_overage(components[count])
                if overage:
                    slots.remove(c)
                    components = list(cls._distribute_overage(components, overage, slots))
                count += 1

            r = util.clamp(util.round_half_up(components[0]), 0, 255) / 255.0
            g = util.clamp(util.round_half_up(components[1]), 0, 255) / 255.0
            b = util.clamp(util.round_half_up(components[2]), 0, 255) / 255.0
        color.red = r
        color.green = g
        color.blue = b


class ColorTweaker(object):
    """Tweak the color scheme with the provided filter(s)."""

    def __init__(self, filters):
        """Initialize."""

        self.filters = []
        for f in filters.split(";"):
            m = FILTER_MATCH.match(f)
            if m:
                if m.group(1):
                    self.filters.append([m.group(1), float(m.group(2)), m.group(4) if m.group(4) else "all"])
                else:
                    self.filters.append([m.group(3), 0.0, m.group(4) if m.group(4) else "all"])

    def _apply_filter(self, color, f_name, value=None):
        """Apply the filter."""

        if isinstance(color, Color):
            if value is None:
                getattr(_Filters, f_name)(color)
            else:
                getattr(_Filters, f_name)(color, value)

    def _filter_colors(self, *args, **kwargs):
        """Filter the colors."""

        global_settings = kwargs.get("global_settings", False)
        dual_colors = False
        if len(args) == 1:
            fg = args[0]
            bg = None
        elif len(args) == 2:
            fg = args[0]
            bg = args[1]
            if not global_settings:
                dual_colors = True
        else:
            return None, None

        try:
            assert(fg is not None)
            rgba_fg = Color(fg)
        except Exception:
            rgba_fg = fg
        try:
            assert(bg is not None)
            rgba_bg = Color(bg)
        except Exception:
            rgba_bg = bg

        for f in self.filters:
            name = f[0]
            value = f[1]
            context = f[2]
            if name in ("grayscale", "sepia", "invert"):
                if context != "bg":
                    self._apply_filter(rgba_fg, name)
                if context != "fg":
                    self._apply_filter(rgba_bg, name)
            elif name in ("saturation", "brightness", "hue", "colorize", "contrast"):
                if context != "bg":
                    self._apply_filter(rgba_fg, name, value)
                if context != "fg":
                    self._apply_filter(rgba_bg, name, value)
            elif (
                name == "glow" and dual_colors and isinstance(rgba_fg, Color) and
                (bg is None or bg.strip() == "" or bg == "none")
            ):
                rgba = Color(rgba_fg)
                rgba.overlay(self.bground if self.bground != "" else "#FFFFFF", in_place=True)
                bg = rgba.to_string(hex=True, alpha=False) + ("%02X" % int((255.0 * value)))
                try:
                    rgba_bg = Color(bg)
                except Exception:
                    rgba_bg = bg
        return (
            rgba_fg.to_string(hex=True) if isinstance(rgba_fg, Color) else rgba_fg,
            rgba_bg.to_string(hex=True) if isinstance(rgba_bg, Color) else rgba_bg
        )

    def tweak(self, fg=None, bg=None):
        """Tweak the theme with the provided filters."""

        if len(self.filters):
            if fg is None:
                _, value = self._filter_colors(None, self.process_color(bg), global_settings=True)
                if value is None:
                    value = bg
                return None, value
            if bg is None:
                _, value = self._filter_colors(None, self.process_color(fg))
                if value is None:
                    value = fg
                return value, None
            else:
                value1, value2 = self._filter_colors(self.process_color(fg), self.process_color(bg))
                if value1 is None:
                    value1 = fg
                if value2 is None:
                    value2 = bg
                return value1, value2

        return fg, bg

    def process_color(self, color):
        """Process the color."""

        if color is None or color.strip() == "" or color == "none":
            return None

        if not color.startswith('#'):
            return None
        return color

    def get_filters(self):
        """Get the filters."""

        filters = []
        for f in self.filters:
            if f[0] in ("invert", "grayscale", "sepia"):
                filters.append(f[0])
            elif f[0] in ("hue", "colorize"):
                filters.append(f[0] + "(%d)" % int(f[1]))
            elif f[0] in ("saturation", "brightness", "contrast"):
                filters.append(f[0] + "(%f)" % f[1])
            elif f[0] == 'glow':
                filters.append(f[0] + "(%f)" % f[1])
            else:
                continue
            if f[2] != "all":
                filters[-1] = filters[-1] + ("@%s" % f[2])
        return filters


class ColorSchemeTweaker(object):
    """Tweak the color scheme with the provided filter(s)."""

    def _apply_filter(self, color, f_name, value=None):
        """Apply the filter."""

        if isinstance(color, Color):
            if value is None:
                getattr(_Filters, f_name)(color)
            else:
                getattr(_Filters, f_name)(color, value)

    def _filter_colors(self, *args, **kwargs):
        """Filter the colors."""

        global_settings = kwargs.get("global_settings", False)
        dual_colors = False
        if len(args) == 1:
            fg = args[0]
            bg = None
        elif len(args) == 2:
            fg = args[0]
            bg = args[1]
            if not global_settings:
                dual_colors = True
        else:
            return None, None

        try:
            assert(fg is not None)
            rgba_fg = Color(fg)
        except Exception:
            rgba_fg = fg
        try:
            assert(bg is not None)
            rgba_bg = Color(bg)
        except Exception:
            rgba_bg = bg

        for f in self.filters:
            name = f[0]
            value = f[1]
            context = f[2]
            if name in ("grayscale", "sepia", "invert"):
                if context != "bg":
                    self._apply_filter(rgba_fg, name)
                if context != "fg":
                    self._apply_filter(rgba_bg, name)
            elif name in ("saturation", "brightness", "hue", "colorize", "contrast"):
                if context != "bg":
                    self._apply_filter(rgba_fg, name, value)
                if context != "fg":
                    self._apply_filter(rgba_bg, name, value)
            elif (
                name == "glow" and dual_colors and isinstance(rgba_fg, Color) and
                (bg is None or bg.strip() == "" or bg == "none")
            ):
                rgba = Color(rgba_fg)
                rgba.overlay(self.bground if self.bground != "" else "#FFFFFF", in_place=True)
                bg = rgba.to_string(hex=True, alpha=False) + ("%02X" % int((255.0 * value)))
                try:
                    rgba_bg = Color(bg)
                except Exception:
                    rgba_bg = bg
        return (
            rgba_fg.to_string(hex=True) if isinstance(rgba_fg, Color) else rgba_fg,
            rgba_bg.to_string(hex=True) if isinstance(rgba_bg, Color) else rgba_bg
        )

    def tweak(self, scheme, filters, tmtheme=False):
        """Tweak the theme with the provided filters."""

        self.filters = []
        for f in filters.split(";"):
            m = FILTER_MATCH.match(f)
            if m:
                if m.group(1):
                    self.filters.append([m.group(1), float(m.group(2)), m.group(4) if m.group(4) else "all"])
                else:
                    self.filters.append([m.group(3), 0.0, m.group(4) if m.group(4) else "all"])

        if len(self.filters):
            for k, v in scheme[GLOBAL_OPTIONS].items():
                if not k.endswith('Css'):
                    if k in ("background", "gutter", "lineHighlight", "selection"):
                        _, value = self._filter_colors(None, self.process_color(v), global_settings=True)
                    else:
                        value, _ = self._filter_colors(self.process_color(v), global_settings=True)
                    if value is None:
                        value = v
                else:
                    value = v
                scheme[GLOBAL_OPTIONS][k] = value

            self.bground = Color(
                self.process_color(
                    scheme[GLOBAL_OPTIONS].get("background", '#FFFFFF')
                )
            ).to_string(hex=True, alpha=False)
            self.fground = Color(
                self.process_color(
                    scheme[GLOBAL_OPTIONS].get("foreground", '#000000')
                )
            ).to_string(hex=True)

            for rule in scheme['rules']:
                fg = rule.get("foreground", None)
                bg = self.process_color(rule.get("background", None))
                if isinstance(fg, list):
                    foreground = []
                    f, background = self._filter_colors((self.process_color(fg[0]) if fg else None), bg)
                    if f:
                        foreground.append(f)
                    for gradient in fg[1:]:
                        f = self._filter_colors(self.process_color(gradient), bg)[0]
                        if f:
                            foreground.append(f)
                    if not foreground:
                        foreground = None
                else:
                    foreground, background = self._filter_colors(self.process_color(fg), bg)
                if foreground is not None:
                    rule["foreground"] = foreground
                if background is not None:
                    rule["background"] = background

        return scheme if not tmtheme else get_tmtheme(scheme)

    def process_color(self, color):
        """Process the color."""

        if color is None or color.strip() == "" or color == "none":
            return None

        if not color.startswith('#'):
            return None
        return color

    def get_filters(self):
        """Get the filters."""

        filters = []
        for f in self.filters:
            if f[0] in ("invert", "grayscale", "sepia"):
                filters.append(f[0])
            elif f[0] in ("hue", "colorize"):
                filters.append(f[0] + "(%d)" % int(f[1]))
            elif f[0] in ("saturation", "brightness", "contrast"):
                filters.append(f[0] + "(%f)" % f[1])
            elif f[0] == 'glow':
                filters.append(f[0] + "(%f)" % f[1])
            else:
                continue
            if f[2] != "all":
                filters[-1] = filters[-1] + ("@%s" % f[2])
        return filters
