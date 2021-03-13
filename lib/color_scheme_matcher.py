"""
color_scheme_matcher.

Licensed under MIT.

Copyright (C) 2012  Andrew Gibson <agibsonsw@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of
the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---------------------

Original code has been heavily modified by Isaac Muse <isaacmuse@gmail.com> for the `ExportHtml` project.
Algorithm has been split out into a separate library and been enhanced with a number of features.
"""
from __future__ import absolute_import
import sublime
import codecs
import re
from .file_strip.json import sanitize_json
from .st_colormod import Color
from .tmtheme import ColorSRGBX11
from os import path
from collections import namedtuple
from plistlib import readPlistFromBytes

NEW_SCHEMES = int(sublime.version()) >= 3150
FONT_STYLE = "font_style" if int(sublime.version()) >= 3151 else "fontStyle"
GLOBAL_OPTIONS = "globals" if int(sublime.version()) >= 3152 else "defaults"

CONVERT_TURN = 360
CONVERT_GRAD = 90 / 100

# XML
XML_COMMENT_RE = re.compile(br"^[\r\n\s]*<!--[\s\S]*?-->[\s\r\n]*|<!--[\s\S]*?-->")

RE_CAMEL_CASE = re.compile('[A-Z]')

HEX = {"hex": True, "alpha": True}
HEX_NA = {"hex": True, "alpha": False}


def packages_path(pth):
    """Get packages path."""

    return path.join(path.dirname(sublime.packages_path()), path.normpath(pth))


def to_snake(m):
    """Convert to snake case."""

    return '_' + m.group(0).lower()


def sublime_format_path(pth):
    """Format path for sublime internal use."""

    m = re.match(r"^([A-Za-z]{1}):(?:/|\\)(.*)", pth)
    if sublime.platform() == "windows" and m is not None:
        pth = m.group(1) + "/" + m.group(2)
    return pth.replace("\\", "/")


class SchemeColors(
    namedtuple(
        'SchemeColors',
        [
            'fg', 'fg_simulated', 'bg', "bg_simulated", "style", "color_gradient",
            "fg_selector", "bg_selector", "style_selectors", "color_gradient_selector"
        ]
    )
):
    """Scheme colors."""


class SchemeSelectors(namedtuple('SchemeSelectors', ['name', 'scope'], verbose=False)):
    """Scheme selectors."""


class ColorSchemeMatcher(object):
    """Determine color scheme colors and style for text in a Sublime view buffer."""

    def __init__(self, scheme_file, color_filter=None):
        """Initialize."""
        if color_filter is None:
            color_filter = self.filter
        self.color_scheme = scheme_file.replace('\\', '/')
        self.scheme_file = path.basename(self.color_scheme)

        if NEW_SCHEMES and scheme_file.endswith(('.sublime-color-scheme', '.hidden-color-scheme')):
            self.legacy = False
            self.scheme_obj = {
                'variables': {},
                GLOBAL_OPTIONS: {},
                'rules': []
            }
        else:
            try:
                content = sublime.load_binary_resource(sublime_format_path(self.color_scheme))
            except IOError:
                # Fallback if file was created manually and not yet found in resources
                with open(packages_path(self.color_scheme), 'rb') as f:
                    content = f.read()
            self.legacy = True
            self.convert_format(readPlistFromBytes(XML_COMMENT_RE.sub(b'', content)))
        self.overrides = []
        if NEW_SCHEMES:
            self.merge_overrides()
        self.scheme_file = scheme_file
        self.matched = {}
        self.variables = {}
        self.parse_scheme()
        self.scheme_obj = color_filter(self.scheme_obj)
        self.setup_matcher()

    def convert_format(self, obj):
        """Convert `tmTheme` object to new format."""

        self.scheme_obj = {
            "variables": {},
            GLOBAL_OPTIONS: {},
            "rules": []
        }

        for k, v in obj.items():
            if k == "settings":
                continue
            self.scheme_obj[k] = v

        for item in obj["settings"]:
            if item.get('scope', None) is None and item.get('name', None) is None:
                for k, v in item["settings"].items():
                    try:
                        v = ColorSRGBX11(v).to_string(hex=True)
                    except Exception:
                        pass
                    self.scheme_obj[GLOBAL_OPTIONS][RE_CAMEL_CASE.sub(to_snake, k)] = v
            if 'settings' in item and item.get('scope') is not None:
                rule = {}
                name = item.get('name')
                if name is not None:
                    rule['name'] = name
                scope = item.get('scope')
                if scope is not None:
                    rule["scope"] = scope
                fg = item['settings'].get('foreground')
                if fg is not None:
                    rule['foreground'] = ColorSRGBX11(fg).to_string(hex=True)
                bg = item['settings'].get('background')
                if bg is not None:
                    rule['background'] = ColorSRGBX11(bg).to_string(hex=True)
                selfg = item["settings"].get("selectionForeground")
                if selfg is not None:
                    rule["selection_foreground"] = ColorSRGBX11(selfg).to_string(hex=True)
                font_style = item["settings"].get('fontStyle')
                if font_style is not None:
                    rule[FONT_STYLE] = font_style
                self.scheme_obj['rules'].append(rule)

    def merge_overrides(self):
        """Merge override schemes."""

        package_overrides = []
        user_overrides = []
        if self.scheme_file.endswith('.hidden-color-scheme'):
            pattern = '%s.hidden-color-scheme'
        else:
            pattern = '%s.sublime-color-scheme'
        for override in sublime.find_resources(pattern % path.splitext(self.scheme_file)[0]):
            if override.startswith('Packages/User/'):
                user_overrides.append(override)
            else:
                package_overrides.append(override)
        for override in (package_overrides + user_overrides):
            try:
                ojson = sublime.decode_value(sublime.load_resource(override))
            except IOError:
                # Fallback if file was created manually and not yet found in resources
                # Though it is unlikely this would ever get executed as `find_resources`
                # probably wouldn't have seen it either.
                with codecs.open(packages_path(override), 'r', encoding='utf-8') as f:
                    ojson = sublime.decode_value(sanitize_json(f.read()))

            for k, v in ojson.get('variables', {}).items():
                self.scheme_obj['variables'][k] = v

            for k, v in ojson.get(GLOBAL_OPTIONS, {}).items():
                self.scheme_obj[GLOBAL_OPTIONS][k] = v

            for item in ojson.get('rules', []):
                self.scheme_obj['rules'].append(item)

            self.overrides.append(override)

        # Rare case of being given a file but sublime hasn't indexed the files and can't find it
        if (
            not self.overrides and
            self.color_scheme.endswith(('.sublime-color-scheme', '.hidden-color-scheme')) and
            self.color_scheme.startswith('Packages/')
        ):
            with codecs.open(packages_path(self.color_scheme), 'r', encoding='utf-8') as f:
                ojson = sublime.decode_value(sanitize_json(f.read()))

                for k, v in ojson.get('variables', {}).items():
                    self.scheme_obj['variables'][k] = v

                for k, v in ojson.get(GLOBAL_OPTIONS, {}).items():
                    self.scheme_obj[GLOBAL_OPTIONS][k] = v

                for item in ojson.get('rules', []):
                    self.scheme_obj['rules'].append(item)

                self.overrides.append(self.color_scheme)

    def filter(self, scheme):  # noqa A003
        """Dummy filter call that does nothing."""

        return scheme

    def parse_scheme(self):
        """Parse the color scheme."""

        variables = self.scheme_obj.get('variables', {})
        for k, v in variables.items():
            # m = COLOR_RE.match(v.strip())
            try:
                var = Color(v, variables=self.scheme_obj.get('variables'))
            except Exception:
                var = None
            # var = translate_color(m, self.variables, self.scheme_obj.get('variables')) if m is not None else ""
            if var is None:
                var = ""
            self.variables[k] = var.convert("srgb").to_string(**HEX) if var else var
            variables[k] = self.variables[k]

        global_options = self.scheme_obj[GLOBAL_OPTIONS]
        for k, v in global_options.items():
            try:
                global_color = Color(v.strip(), variables=self.variables)
            except Exception:
                global_color = None
            if global_color is not None:
                global_options[k] = global_color.convert("srgb").to_string(**HEX)

        # Create scope colors mapping from color scheme file
        for item in self.scheme_obj["rules"]:
            if item.get('scope', None) is not None:
                # Foreground color
                color = item.get('foreground', None)
                if isinstance(color, list):
                    # Hashed Syntax Highlighting
                    try:
                        for index, c in enumerate(color):
                            color[index] = Color(
                                c.strip(), variables=self.variables
                            ).convert("srgb").to_string(**HEX)
                    except Exception:
                        item['foreground'] = "none"
                elif isinstance(color, str):
                    try:
                        item['foreground'] = Color(
                            color.strip(), variables=self.variables
                        ).convert("srgb").to_string(**HEX)
                    except Exception:
                        item['foreground'] = "none"
                # Background color
                bgcolor = item.get('background', None)
                if isinstance(bgcolor, str):
                    try:
                        item['background'] = Color(
                            bgcolor.strip(), variables=self.variables
                        ).convert("srgb").to_string(**HEX)
                        fgadj = item.get('foreground_adjust', None)
                        if isinstance(fgadj, str) and fgadj:
                            item['foreground_adjust'] = fgadj
                    except Exception:
                        pass
                # Selection foreground color
                scolor = item.get('selection_foreground', None)
                if isinstance(scolor, str):
                    try:
                        item['selection_foreground'] = Color(
                            scolor.strip(), variables=self.variables
                        ).convert("srgb").to_string(**HEX)
                    except Exception:
                        pass

    def setup_matcher(self):
        """Setup colors for color matcher."""

        color_settings = {}
        global_options = self.scheme_obj[GLOBAL_OPTIONS]
        for k, v in global_options.items():
            if v.startswith('#'):
                color_settings[k] = v

        # Get general theme colors from color scheme file
        bground, bground_sim = self.process_color(
            color_settings.get("background", '#FFFFFF'), simple_strip=True
        )

        # Need to set background so other colors can simulate their transparency.
        self.special_colors = {
            "background": {'color': bground, 'color_simulated': bground_sim}
        }

        fground, fground_sim = self.process_color(color_settings.get("foreground", '#000000'))
        sbground, sbground_sim = self.process_color(color_settings.get("selection", "#0000FF"))
        sfground, sfground_sim = self.process_color(color_settings.get("selection_foreground", None))
        gbground = self.process_color(color_settings.get("gutter", bground))[0]
        gbground_sim = self.process_color(color_settings.get("gutter", bground_sim))[1]
        gfground = self.process_color(color_settings.get("gutter_foreground", fground))[0]
        gfground_sim = self.process_color(color_settings.get("gutter_foreground", fground_sim))[1]

        self.special_colors["foreground"] = {'color': fground, 'color_simulated': fground_sim}
        self.special_colors["background"] = {'color': bground, 'color_simulated': bground_sim}
        self.special_colors["selection_foreground"] = {'color': sfground, 'color_simulated': sfground_sim}
        self.special_colors["selection"] = {'color': sbground, 'color_simulated': sbground_sim}
        self.special_colors["gutter"] = {'color': gbground, 'color_simulated': gbground_sim}
        self.special_colors["gutter_foreground"] = {'color': gfground, 'color_simulated': gfground_sim}
        self.colors = {}
        # Create scope colors mapping from color scheme file
        for item in self.scheme_obj["rules"]:
            name = item.get('name', '')
            scope = item.get('scope', None)
            color = None
            bgcolor = None
            fgadj = None
            scolor = None
            style = []
            if scope is not None:
                # Foreground color
                color = item.get('foreground', None)
                # Background color
                bgcolor = item.get('background', None)
                if bgcolor:
                    fgadj = item.get('foreground_adjust', None)
                # Selection foreground color
                scolor = item.get('selection_foreground', None)
                # Font style
                if FONT_STYLE in item:
                    for s in item.get(FONT_STYLE, '').split(' '):
                        if s in ('bold', 'italic', 'underline', 'glow'):
                            style.append(s)

                self.add_entry(name, scope, color, bgcolor, fgadj, scolor, style)

    def add_entry(self, name, scope, color, bgcolor, fgadj, scolor, style):
        """Add color entry."""

        color_gradient = None
        if isinstance(color, list):
            fg, fg_sim, color_gradient = self.process_color_gradient(color)
        elif color is not None:
            if color == "none":
                fg, fg_sim = color, None
            else:
                fg, fg_sim = self.process_color(color)
        else:
            fg, fg_sim = None, None
        if bgcolor is not None:
            bg, bg_sim = self.process_color(bgcolor)
        else:
            bg, bg_sim = None, None
        if scolor is not None:
            if scolor == "none":
                sfg, sfg_sim = scolor, None
            else:
                sfg, sfg_sim = self.process_color(
                    scolor, bground=self.special_colors["selection"]['color_simulated']
                )
        else:
            sfg, sfg_sim = None, None
        self.colors[scope] = {
            "name": name,
            "scope": scope,
            "color": fg,
            "color_simulated": fg_sim,
            "color_gradient": color_gradient,
            "bgcolor": bg,
            "bgcolor_simulated": bg_sim,
            "selection_color": sfg,
            "selection_color_simulated": sfg_sim,
            "style": style,
            "foreground_adjust": fgadj
        }

    def process_color_gradient(self, colors, simple_strip=False, bground=None):
        """
        Strip transparency from the color gradient list.

        Transparency can be stripped in one of two ways:
            - Simply mask off the alpha channel.
            - Apply the alpha channel to the color essential getting the color seen by the eye.
        """

        gradient = []

        for color in colors:
            if color is None or color.strip() == "":
                continue

            if not color.startswith('#'):
                continue

            rgb = Color(color.replace(" ", ""))
            if not simple_strip:
                if bground is None:
                    bground = self.special_colors['background']['color_simulated']
                rgb.overlay(Color(bground if bground != "" else "#FFFFFF"))

            gradient.append((color, rgb.to_string(**HEX)))
        if gradient:
            color, color_sim = gradient[0]
            return color, color_sim, gradient
        else:
            return None, None, None

    def process_color(self, color, simple_strip=False, bground=None):
        """
        Strip transparency from the color value.

        Transparency can be stripped in one of two ways:
            - Simply mask off the alpha channel.
            - Apply the alpha channel to the color essential getting the color seen by the eye.
        """

        if color is None or color.strip() == "":
            return None, None

        if not color.startswith('#'):
            return None, None

        rgb = Color(color.replace(" ", ""))
        if not simple_strip:
            if bground is None:
                bground = self.special_colors['background']['color_simulated']
            rgb.overlay(Color(bground if bground != "" else "#FFFFFF"))

        return color, rgb.to_string(**HEX)

    def get_special_color(self, name, simulate_transparency=False):
        """
        Get the core colors (background, foreground) for the view and gutter.

        Get the visible look of the color by simulated transparency if requested.
        """

        name = RE_CAMEL_CASE.sub(to_snake, name)
        return self.special_colors.get(name, {}).get('color_simulated' if simulate_transparency else 'color')

    def get_scheme_obj(self):
        """Get the scheme file used during the process."""

        return self.scheme_obj

    def get_scheme_file(self):
        """Get the scheme file used during the process."""

        return self.scheme_file

    def guess_color(self, scope_key, selected=False, explicit_background=False, no_bold=False, no_italic=False):
        """
        Guess the colors and style of the text for the given Sublime scope.

        By default, we always fall back to the schemes default background,
        but if desired, we can show that no background was explicitly
        specified by returning None.  This is done by enabling explicit_background.
        This will only show backgrounds that were explicitly specified.

        This was originally introduced for mdpopups so that it would
        know when a background was not needed.  This allowed mdpopups
        to generate syntax highlighted code that could be overlayed on
        block elements with different background colors and allow that
        background would show through.
        """

        color = self.special_colors['foreground']['color']
        color_sim = self.special_colors['foreground']['color_simulated']
        color_gradient = None
        color_gradient_selector = None
        bgcolor = self.special_colors['background']['color'] if not explicit_background else None
        bgcolor_sim = self.special_colors['background']['color_simulated'] if not explicit_background else None
        fgadj = None
        scolor = self.special_colors['selection_foreground']['color']
        scolor_sim = self.special_colors['selection_foreground']['color_simulated']
        style = set([])
        color_selector = SchemeSelectors("foreground", "foreground")
        bg_selector = SchemeSelectors("background", "background")
        scolor_selector = SchemeSelectors("selection_foreground", "selection_foreground")
        style_selectors = {
            "bold": SchemeSelectors("", ""),
            "italic": SchemeSelectors("", ""),
            "underline": SchemeSelectors("", ""),
            "glow": SchemeSelectors("", "")
        }
        if scope_key in self.matched:
            color = self.matched[scope_key]["color"]
            color_sim = self.matched[scope_key]["color_simulated"]
            color_gradient = self.matched[scope_key]["color_gradient"]
            style = self.matched[scope_key]["style"]
            bgcolor = self.matched[scope_key]["bgcolor"]
            bgcolor_sim = self.matched[scope_key]["bgcolor_simulated"]
            scolor = self.matched[scope_key]["scolor"]
            scolor_sim = self.matched[scope_key]["scolor_simulated"]
            selectors = self.matched[scope_key]["selectors"]
            color_selector = selectors["color"]
            bg_selector = selectors["background"]
            scolor_selector = selectors["scolor"]
            style_selectors = selectors["style"]
            color_gradient_selector = selectors['color_gradient']
        else:
            best_match_bg = 0
            best_match_fg = 0
            best_match_style = 0
            best_match_sfg = 0
            best_match_fg_gradient = 0
            for key in self.colors:
                match = sublime.score_selector(scope_key, key)
                if (
                    not self.colors[key]['color_gradient'] and
                    self.colors[key]["color"] is not None and
                    match > best_match_fg
                ):
                    best_match_fg = match
                    color = self.colors[key]["color"]
                    if color == "none":
                        color = self.special_colors['foreground']['color']
                        color_sim = self.special_colors['foreground']['color_simulated']
                    else:
                        color_sim = self.colors[key]["color_simulated"]
                    color_selector = SchemeSelectors(self.colors[key]["name"], self.colors[key]["scope"])
                elif (
                    self.colors[key]["color_gradient"] is not None and
                    match > best_match_fg_gradient
                ):
                    best_match_fg_gradient = match
                    color_gradient = self.colors[key]["color_gradient"]
                    color_gradient_selector = SchemeSelectors(self.colors[key]["name"], self.colors[key]["scope"])
                if self.colors[key]["selection_color"] is not None and match > best_match_sfg:
                    best_match_sfg = match
                    scolor = self.colors[key]["selection_color"]
                    if color == "none":
                        scolor = self.special_colors['selection_foreground']['color']
                        scolor_sim = self.special_colors['selection_foreground']['color_simulated']
                    else:
                        scolor_sim = self.colors[key]["selection_color_simulated"]
                    scolor_selector = SchemeSelectors(self.colors[key]["name"], self.colors[key]["scope"])
                if self.colors[key]["style"] is not None and match > best_match_style:
                    best_match_style = match
                    for s in self.colors[key]["style"]:
                        if not (s == "bold" and no_bold) and not (s == "italic" and no_italic):
                            style.add(s)
                        if s == "bold":
                            style_selectors["bold"] = SchemeSelectors(
                                self.colors[key]["name"], self.colors[key]["scope"]
                            )
                        elif s == "italic":
                            style_selectors["italic"] = SchemeSelectors(
                                self.colors[key]["name"], self.colors[key]["scope"]
                            )
                        elif s == "underline":
                            style_selectors["underline"] = SchemeSelectors(
                                self.colors[key]["name"], self.colors[key]["scope"]
                            )
                        elif s == "glow":
                            style_selectors["glow"] = SchemeSelectors(
                                self.colors[key]["name"], self.colors[key]["scope"]
                            )
                if self.colors[key]["bgcolor"] is not None and match > best_match_bg:
                    best_match_bg = match
                    bgcolor = self.colors[key]["bgcolor"]
                    bgcolor_sim = self.colors[key]["bgcolor_simulated"]
                    fgadj = self.colors[key]["foreground_adjust"]
                    bg_selector = SchemeSelectors(self.colors[key]["name"], self.colors[key]["scope"])

            if len(style) == 0:
                style = ""
            else:
                style = ' '.join(style)

            if not isinstance(color_gradient, list):
                color_gradient = None
                color_gradient_selector = None

            if fgadj is not None:
                for c in (color_gradient if color_gradient is not None else [color]):
                    color_list = []
                    try:
                        content = 'color({} {})'.format(c, fgadj)
                        content = Color(content, variables=self.variables).convert("srgb").to_string(**HEX)
                        if c != content:
                            mod, mod_sim = self.process_color(content)
                            if mod is not None:
                                color_list.append((mod, mod_sim))
                        color_gradient = color_list
                        color, color_sim = color_gradient[0]
                    except Exception:
                        pass

            self.matched[scope_key] = {
                "color": color,
                "bgcolor": bgcolor,
                "scolor": scolor,
                "color_simulated": color_sim,
                "bgcolor_simulated": bgcolor_sim,
                "scolor_simulated": scolor_sim,
                "color_gradient": color_gradient,
                "style": style,
                "selectors": {
                    "color": color_selector,
                    "background": bg_selector,
                    "scolor": scolor_selector,
                    "style": style_selectors,
                    "color_gradient": color_gradient_selector
                }
            }

        if selected:
            if scolor:
                color = scolor
                color_sim = scolor_sim
                color_selector = scolor_selector
                color_gradient = None
                color_gradient_selector = None
            if self.special_colors['selection']['color']:
                bgcolor = self.special_colors['selection']['color']
                bgcolor_sim = self.special_colors['selection']['color_simulated']
                bg_selector = SchemeSelectors("selection", "selection")

        return SchemeColors(
            color, color_sim, bgcolor, bgcolor_sim, style, color_gradient,
            color_selector, bg_selector, style_selectors, color_gradient_selector
        )
