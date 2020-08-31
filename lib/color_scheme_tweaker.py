"""
Color Scheme Tweaker (for sublime text).

Licensed under MIT
Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
from __future__ import absolute_import
import sublime
from .colorcss import RGB
from . import x11colors
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


class ColorSchemeTweaker(object):
    """Tweak the color scheme with the provided filter(s)."""

    def _apply_filter(self, color, f_name, value=None):
        """Apply the filter."""

        if isinstance(color, RGB):
            if value is None:
                color.__getattribute__(f_name)()
            else:
                color.__getattribute__(f_name)(value)

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
            rgba_fg = RGB(fg)
        except Exception:
            rgba_fg = fg
        try:
            assert(bg is not None)
            rgba_bg = RGB(bg)
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
            elif name == "glow" and dual_colors and isinstance(rgba_fg, RGB) and (bg is None or bg.strip() == ""):
                rgba = RGB(rgba_fg)
                rgba.apply_alpha(RGB(self.bground if self.bground != "" else "#FFFFFF"))
                bg = rgba.to_css(prefer_hex=True) + ("%02X" % int((255.0 * value)))
                try:
                    rgba_bg = RGB(bg)
                except Exception:
                    rgba_bg = bg
        return (
            rgba_fg.to_css(prefer_hex=True, alpha=True) if isinstance(rgba_fg, RGB) else rgba_fg,
            rgba_bg.to_css(prefer_hex=True, alpha=True) if isinstance(rgba_bg, RGB) else rgba_bg
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

            self.bground = RGB(
                self.process_color(
                    scheme[GLOBAL_OPTIONS].get("background", '#FFFFFF')
                )
            ).to_css(prefer_hex=True)
            self.fground = RGB(
                self.process_color(
                    scheme[GLOBAL_OPTIONS].get("foreground", '#000000')
                )
            ).to_css(prefer_hex=True, alpha=True)

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

        if color is None or color.strip() == "":
            return None

        if not color.startswith('#'):
            color = x11colors.name2hex(color)
            if color is None:
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
