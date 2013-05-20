import sublime
import sublime_plugin
from os import path
import tempfile
import sys
import time
import webbrowser
import re
from HtmlAnnotations import get_annotations
import ExportHtmlLib.desktop as desktop
import json

PACKAGE_SETTINGS = "ExportHtml.sublime-settings"
JS_DIR = path.join(sublime.packages_path(), 'ExportHtml', "js")
CSS_DIR = path.join(sublime.packages_path(), 'ExportHtml', "css")

if sublime.platform() == "linux":
    # Try and load Linux Python2.6 lib.  Default path is for Ubuntu.
    linux_lib = sublime.load_settings(PACKAGE_SETTINGS).get("linux_python2.6_lib", "/usr/lib/python2.6/lib-dynload")
    if not linux_lib in sys.path and path.exists(linux_lib):
        sys.path.append(linux_lib)
from plistlib import readPlist
from ExportHtmlLib.rgba.rgba import RGBA

FILTER_MATCH = re.compile(r'^(?:(brightness|saturation|hue|colorize)\((-?[\d]+|[\d]*\.[\d]+)\)|(sepia|grayscale|invert))$')

# HTML Code
HTML_HEADER = \
'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<title>%(title)s</title>
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
<meta http-equiv="Pragma" content="no-cache" />
<meta http-equiv="Expires" content="0" />
<style type="text/css">
%(css)s
</style>
%(js)s
</head>
'''

TOOL_GUTTER = '''<img onclick="toggle_gutter();" alt="" title="Toggle Gutter" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3AofFg8FBLseHgAAAAxpVFh0Q29tbWVudAAAAAAAvK6ymQAAAM5JREFUOMvdjzFqAlEQhuephZWNYEq9wJ4kt7C08AiyhWCXQI6xh5CtUqVJEbAU1kA6i92VzWPnmxR5gUUsfAQbf5himPm+YURumSzLetFQWZZj4Bn45DcHYFMUxfAqAbA1MwO+gHeA0L9cJfDeJ6q6yvO8LyKiqosgOKVp6qJf8t4nQfD9J42Kqi6D4DUabppmBhzNzNq2fYyC67p+AHbh+iYKrqpqAnwE+Ok/8Dr6b+AtwArsu6Wq8/P9wQXHTETEOdcTkWl3YGYjub/8ANrnvguZ++ozAAAAAElFTkSuQmCC" />'''

TOOL_PLAIN_TEXT = '''<img onclick="toggle_plain_text();" alt="" title="Toggle Plain" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3AofFg8dF9eGSAAAAAxpVFh0Q29tbWVudAAAAAAAvK6ymQAAANRJREFUOMvdkTFOgkEQhResaeQScAsplIRGDgKttnsIOYIUm1hQa/HfQiMFcIBt9k/UTWa/sRkbspKfzviS7eZ7M/uec39WbdsOgU/gI6V0ebZBKeVeTaWUu7PgpmkugD3wZW8XQuh3NhCRuaoq8AisVVVF5LazAfBi0JWITMzsuROccx4b8O6cc977HrAFyDmPumxfHQf3EyjwcBKOMQ6ApL8ISDHGwanqljb4VLlsY5ctqrD99c3Cm1aamZn5q/e+V6vuxgb2tc5DCH3gYAuu3f/RNzmJ99G3cZ53AAAAAElFTkSuQmCC" />'''

TOOL_PRINT = '''<img onclick="page_print();" alt="" title="Print" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3AofFhAl8o8wSAAAAAxpVFh0Q29tbWVudAAAAAAAvK6ymQAAAQZJREFUOMulkzFSgjEUhL8X/xJ/iBegkAtQ6A08gIUehFthYykOw9BzBmwcaxGoZW1eZjIx/sC4TTJv8ja7mxfDIcmAAWDUIeDLzJQXm2w/AFZOkB8yoAU+gHtJ7yVJUnAlaS1pJOm6WN8kjSUtJQ1dLQChIvMATIEXXw9e3wMT4NnV/rKQsAcegAvgG9g5wcwv7OU51QgugSegD2yBO+DWmyLw+leINQXyW5VeoQj4qIIcW+CxPFwjSLKtEnAZOkGSSYruL3QMUxq0AERJUZKl5pV7bjsmMR+qHfAJ3DReDB4cwKLiv0R0S5Yy6ANz37ecgSZ7nui1zYm9G0B2wi+k63fyX/wA0b9vjF8iB3oAAAAASUVORK5CYII=" />'''

TOOL_ANNOTATION = '''<img onclick="toggle_annotations();" alt="" title="Toggle Annotations" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3AofFhAIt1BsPQAAAAxpVFh0Q29tbWVudAAAAAAAvK6ymQAAALVJREFUOMvNkkESgjAUQ/Or+8IN9A7ewHN7FRgvwIB7eW6+WGsRRjZm05n+Jn+aRNoIyy8Ak1QVZkjqzYyiQEKsJF0kxUxgkHSW1Eu6mdn9bStwABqgA0Y+MfqsBU7ALie3M8SS0NU5JqD2zWvIqUgD1MF9iCVDF8yPkixsjTF4PIOfa/Hi/GhiO5mYJHH0mL4ROzdvIu+TAoW8ddm30iJNjTQgevOqpMLPx8NilWe6X3z8n3gAfmBJ5rRJVyQAAAAASUVORK5CYII=" />'''

TOOL_DUMP_THEME = '''<img onclick="dump_theme();" alt="" title="Download" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3AofFhAWTV9RXgAAAAxpVFh0Q29tbWVudAAAAAAAvK6ymQAAAJtJREFUOMvdk9ENwyAQQ5+rDBA6QZbI/gN0h3YE2gXi/lykhABN1b9aQkh3+CEwiEK2BYyAyhbwlORtceCoEbgBqahnYI65C1CYr43eThd+1B8Ahkp0qXZZa8/2LlIFIG2i676DmDMwS8pDcZzW7tt4DbwOr8/2ZPthe3FbS6yZ4thfQdrmE5DP5g7kvLkCucdomtWDRJzUvvGqN6JK1cOooSjlAAAAAElFTkSuQmCC" />'''

TOOL_WRAPPING = '''<img onclick="toggle_wrapping();" alt="" title="Toggle Wrapping" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3AsBFiYl9jWoIQAAAAxpVFh0Q29tbWVudAAAAAAAvK6ymQAAAP1JREFUOMudk0FuwkAMRZ+jbCGZXADlKvS8HKG9Qa8Q1K5LSLpG+ixwUmdKQMLSSDOeb/v7e8bITJIBNWD5FTCYmaLT7gTWwDtQZQlG4A0YYiILwTvgwxNsgV+vOuEm3wDsga+ZjaQkqZN0kdT7vpXU+Grd1zumk5Rm6g44STr6PjmriEl+d3RsK8li9T/nimXFOkmp8P4mwcZc5YXit7vRjxVgBQ/MK1aPWBWu9Jw1A9c+mZ0nW7AFdLevwKCR9BPE/SdiaWaSNADntdb9jXz6eQt8L15lGFM+vsarRevjtMqg7pkXrHghZiFs+QS8xmwDHIC9PXsHK197/t5XQswlGeOCYgkAAAAASUVORK5CYII=" />'''

TOOLBAR = '''<div id="toolbarhide"><div id="toolbar">%(options)s</div></div>'''

ANNOTATE_OPEN = '''<span onclick="toggle_annotations();" class="tooltip_hotspot" onmouseover="tooltip.show(%(comment)s);" onmouseout="tooltip.hide();">%(code)s'''

ANNOTATE_CLOSE = '''</span>'''

BODY_START = '''<body class="code_page code_text"><pre class="code_page">'''

FILE_INFO = '''<tr><td colspan="2"><div id="file_info"><span style="color: %(color)s">%(date_time)s %(file)s\n\n</span></div></td></tr>'''

TABLE_START = '''<table cellspacing="0" cellpadding="0" class="code_page">'''

LINE = (
    '<tr>' +
    '<td valign="top" id="L_%(table)d_%(line_id)d" class="code_text code_gutter">' +
    '<span style="color: %(color)s;">%(line)s&nbsp;</span>' +
    '</td>' +
    '<td valign="top" class="code_text code_line" style="background-color: %(pad_color)s;">' +
    '<div id="C_%(table)d_%(code_id)d">%(code)s\n</div>' +
    '</td>' +
    '</tr>'
)

CODE = '''<span class="%(class)s" style="background-color: %(highlight)s; color: %(color)s;">%(content)s</span>'''
ANNOTATION_CODE = '''<span style="background-color: %(highlight)s;"><a href="javascript:void();" class="annotation"><span class="%(class)s annotation" style="color: %(color)s;">%(content)s</span></a></span>'''

TABLE_END = '''</table>'''

ROW_START = '''<tr><td>'''

ROW_END = '''</td></tr>'''

DIVIDER = '''<span style="color: %(color)s">\n...\n\n</span>'''

ANNOTATION_TBL_START = (
    '<div id="comment_list" style="display:none"><div id="comment_wrapper">' +
    '<table id="comment_table">' +
    '<tr><th>Line/Col</th><th>Comments' +
    '<a href="javascript:void(0)" class="table_close" onclick="toggle_annotations();return false;">(close)</a>'
    '</th></tr>'
)

ANNOTATION_TBL_END = '''</table></div></div>'''

ANNOTATION_ROW = (
    '<tr>' +
    '<td class="annotation_link">' +
    '<a href="javascript:void(0)" onclick="scroll_to_line(\'C_%(table)d_%(row)d\');return false;">%(link)s</a>' +
    '</td>' +
    '<td class="annotation_comment"><div class="annotation_comment">%(comment)s</div></td>' +
    '<tr>'
)

ANNOTATION_FOOTER = (
    '<tr><td colspan=2>' +
    '<div class="table_footer"><label>Position </label>' +
    '<select id="dock" size="1" onchange="dock_table();">' +
    '<option value="0" selected="selected">center</option>' +
    '<option value="1">top</option>' +
    '<option value="2">bottom</option>' +
    '<option value="3">left</option>' +
    '<option value="4">right</option>' +
    '<option value="5">top left</option>' +
    '<option value="6">top right</option>' +
    '<option value="7">bottom left</option>' +
    '<option value="8">bottom right</option>' +
    '</select>' +
    '</div>' +
    '</td></tr>'
)

BODY_END = '''</pre>%(toolbar)s\n%(js)s\n</body>\n</html>\n'''

INCLUDE_THEME = \
'''
<script type="text/javascript">
%(jscode)s
plist.color_scheme = %(theme)s;

function dump_theme() {
    extract_theme('%(name)s');
}
</script>
'''

TOGGLE_LINE_OPTIONS = \
'''
<script type="text/javascript">
%(jscode)s

page_line_info.wrap      = false;
page_line_info.ranges    = [%(ranges)s];
page_line_info.wrap_size = %(wrap_size)d;
page_line_info.tables    = %(tables)s;
page_line_info.header    = %(header)s;
page_line_info.gutter    = %(gutter)s;
</script>
'''

AUTO_PRINT = \
'''
<script type="text/javascript">
document.getElementsByTagName('body')[0].onload = function (e) { page_print(); self.onload = null; };
</script>
'''

WRAP = \
'''
<script type="text/javascript">
toggle_wrapping();
</script>
'''

HTML_JS_WRAP = \
'''
<script type="text/javascript">
%(jscode)s
</script>
'''


def getjs(file_name):
    code = ""
    try:
        with open(path.join(JS_DIR, file_name), "r") as f:
            code = f.read()
    except:
        pass
    return code


def getcss(file_name, options):
    code = ""
    final_code = ""
    last_pt = 0
    keys = '|'.join(options.keys())
    replace = re.compile("/\\* *%(" + keys + ")% * \\*/")

    try:
        with open(path.join(CSS_DIR, file_name), "r") as f:
            code = f.read()
            for m in replace.finditer(code):
                final_code += code[last_pt:m.start()] + options[m.group(1)]
                last_pt = m.end()
            final_code += code[last_pt:]
    except:
        pass

    return final_code


class ExportHtmlPanelCommand(sublime_plugin.WindowCommand):
    def execute(self, value):
        if value >= 0:
            view = self.window.active_view()
            if view != None:
                ExportHtml(view).run(**self.args[value])

    def run(self):
        options = sublime.load_settings(PACKAGE_SETTINGS).get("html_panel", {})
        menu = []
        self.args = []
        for opt in options:
            k, v = opt.items()[0]
            menu.append(k)
            self.args.append(v)

        if len(menu):
            self.window.show_quick_panel(
                menu,
                self.execute
            )


class ExportHtmlCommand(sublime_plugin.WindowCommand):
    def run(self, **kwargs):
        view = self.window.active_view()
        if view != None:
            ExportHtml(view).run(**kwargs)


class ExportHtml(object):
    def __init__(self, view):
        self.view = view

    def process_inputs(self, **kwargs):
        return {
            "numbers": bool(kwargs.get("numbers", False)),
            "highlight_selections": bool(kwargs.get("highlight_selections", False)),
            "browser_print": bool(kwargs.get("browser_print", False)),
            "color_scheme": kwargs.get("color_scheme", None),
            "wrap": kwargs.get("wrap", None),
            "multi_select": bool(kwargs.get("multi_select", False)),
            "style_gutter": bool(kwargs.get("style_gutter", True)),
            "no_header": bool(kwargs.get("no_header", False)),
            "date_time_format": kwargs.get("date_time_format", "%m/%d/%y %I:%M:%S"),
            "show_full_path": bool(kwargs.get("show_full_path", True)),
            "toolbar": kwargs.get("toolbar", ["plain_text", "gutter", "wrapping", "print", "annotation", "theme"]),
            "save_location": kwargs.get("save_location", None),
            "time_stamp": kwargs.get("time_stamp", "_%m%d%y%H%M%S"),
            "clipboard_copy": bool(kwargs.get("clipboard_copy", False)),
            "view_open": bool(kwargs.get("view_open", False)),
            "shift_brightness": bool(kwargs.get("shift_brightness", False)),
            "filter": kwargs.get("filter", "")
        }

    def setup(self, **kwargs):
        path_packages = sublime.packages_path()

        # Get get general document preferences from sublime preferences
        eh_settings = sublime.load_settings(PACKAGE_SETTINGS)
        settings = sublime.load_settings('Preferences.sublime-settings')
        alternate_font_size = eh_settings.get("alternate_font_size", False)
        alternate_font_face = eh_settings.get("alternate_font_face", False)
        self.font_size = settings.get('font_size', 10) if alternate_font_size == False else alternate_font_size
        self.font_face = settings.get('font_face', 'Consolas') if alternate_font_face == False else alternate_font_face
        self.tab_size = settings.get('tab_size', 4)
        self.padd_top = settings.get('line_padding_top', 0)
        self.padd_bottom = settings.get('line_padding_bottom', 0)
        self.char_limit = int(eh_settings.get("valid_selection_size", 4))
        self.bground = ''
        self.fground = ''
        self.gbground = ''
        self.gfground = ''
        self.sbground = ''
        self.sfground = ''
        self.numbers = kwargs["numbers"]
        self.date_time_format = kwargs["date_time_format"]
        self.time = time.localtime()
        self.show_full_path = kwargs["show_full_path"]
        self.highlight_selections = kwargs["highlight_selections"]
        self.browser_print = kwargs["browser_print"]
        self.auto_wrap = kwargs["wrap"] != None and int(kwargs["wrap"]) > 0
        self.wrap = 900 if not self.auto_wrap else int(kwargs["wrap"])
        self.hl_continue = None
        self.curr_hl = None
        self.sels = []
        self.multi_select = self.check_sel() if kwargs["multi_select"] and not kwargs["highlight_selections"] else False
        self.size = self.view.size()
        self.pt = 0
        self.end = 0
        self.curr_row = 0
        self.tables = 0
        self.curr_annot = None
        self.curr_comment = None
        self.annotations = self.get_annotations()
        self.annot_num = -1
        self.new_annot = False
        self.open_annot = False
        self.no_header = kwargs["no_header"]
        self.annot_tbl = []
        self.toolbar = kwargs["toolbar"]
        self.toolbar_orientation = "block" if eh_settings.get("toolbar_orientation", "horizontal") == "vertical" else "inline-block"
        self.matched = {}
        self.ebground = self.bground
        self.dark_lumens = None
        self.lumens_limit = float(eh_settings.get("bg_min_lumen_threshold", 62))
        self.filter = []
        for f in kwargs["filter"].split(";"):
            m = FILTER_MATCH.match(f)
            if m:
                if m.group(1):
                    self.filter.append((m.group(1), float(m.group(2))))
                else:
                    self.filter.append((m.group(3), 0.0))

        fname = self.view.file_name()
        if fname == None or not path.exists(fname):
            fname = "Untitled"
        self.file_name = fname

        # Get color scheme
        if kwargs["color_scheme"] != None:
            alt_scheme = kwargs["color_scheme"]
        else:
            alt_scheme = eh_settings.get("alternate_scheme", False)
        scheme_file = settings.get('color_scheme') if alt_scheme == False else alt_scheme
        colour_scheme = path.normpath(scheme_file)
        self.scheme_file = path.basename(colour_scheme)
        self.plist_file = self.apply_filters(readPlist(path_packages + colour_scheme.replace('Packages', '')))
        colour_settings = self.plist_file["settings"][0]["settings"]

        # Get general theme colors from color scheme file
        self.bground = self.strip_transparency(colour_settings.get("background", '#FFFFFF'), True, True)
        self.fground = self.strip_transparency(colour_settings.get("foreground", '#000000'))
        self.sbground = self.strip_transparency(colour_settings.get("selection", self.fground), True)
        self.sfground = self.strip_transparency(colour_settings.get("selectionForeground", None))
        self.gbground = self.strip_transparency(colour_settings.get("gutter", self.bground)) if kwargs["style_gutter"] else self.bground
        self.gfground = self.strip_transparency(colour_settings.get("gutterForeground", self.fground), True) if kwargs["style_gutter"] else self.fground

        self.highlights = []
        if self.highlight_selections:
            for sel in self.view.sel():
                if not sel.empty():
                    self.highlights.append(sel)

        # Create scope colors mapping from color scheme file
        self.colours = {self.view.scope_name(self.end).split(' ')[0]: {"color": self.fground, "bgcolor": None, "style": None}}
        for item in self.plist_file["settings"]:
            scope = item.get('scope', None)
            colour = None
            style = []
            if 'scope' in item:
                scope = item['scope']
            if 'settings' in item:
                colour = item['settings'].get('foreground', None)
                bgcolour = item['settings'].get('background', None)
                if 'fontStyle' in item['settings']:
                    for s in item['settings']['fontStyle'].split(' '):
                        if s == "bold" or s == "italic":  # or s == "underline":
                            style.append(s)

            if scope != None and (colour != None or bgcolour != None):
                self.colours[scope] = {
                    "color": self.strip_transparency(colour),
                    "bgcolor": self.strip_transparency(bgcolour, True),
                    "style": style
                }

        self.shift_brightness = kwargs["shift_brightness"] and self.dark_lumens is not None and self.dark_lumens < self.lumens_limit
        if self.shift_brightness:
            self.color_adjust()

    def apply_filters(self, tmtheme):
        def filter_color(color):
            rgba = RGBA(color)
            for f in self.filter:
                name = f[0]
                value = f[1]
                if name == "grayscale":
                    rgba.grayscale()
                elif name == "sepia":
                    rgba.sepia()
                elif name == "saturation":
                    rgba.saturation(value)
                elif name == "invert":
                    rgba.invert()
                elif name == "brightness":
                    rgba.brightness(value)
                elif name == "hue":
                    rgba.hue(value)
                elif name == "colorize":
                    rgba.colorize(value)
            return rgba.get_rgba()

        if len(self.filter):
            general_settings_read = False
            for settings in tmtheme["settings"]:
                if not general_settings_read:
                    for k, v in settings["settings"].items():
                        try:
                            settings["settings"][k] = filter_color(v)
                        except:
                            pass
                    general_settings_read = True
                    continue

                try:
                    settings["settings"]["foreground"] = filter_color(settings["settings"]["foreground"])
                except:
                    pass
                try:
                    settings["settings"]["background"] = filter_color(settings["settings"]["background"])
                except:
                    pass
        return tmtheme

    def color_adjust(self):
        factor = 1 + ((self.lumens_limit - self.dark_lumens) / 255.0) if self.shift_brightness else None
        for k, v in self.colours.items():
            fg, bg = v["color"], v["bgcolor"]
            if v["color"] is not None:
                self.colours[k]["color"] = self.apply_color_change(v["color"], factor)
            if v["bgcolor"] is not None:
                self.colours[k]["bgcolor"] = self.apply_color_change(v["bgcolor"], factor)
        self.bground = self.apply_color_change(self.bground, factor)
        self.fground = self.apply_color_change(self.fground, factor)
        self.sbground = self.apply_color_change(self.sbground, factor)
        if self.sfground is not None:
            self.sfground = self.apply_color_change(self.sfground, factor)
        self.gbground = self.apply_color_change(self.gbground, factor)
        self.gfground = self.apply_color_change(self.gfground, factor)

    def apply_color_change(self, color, shift_factor):
        rgba = RGBA(color)
        if shift_factor is not None:
            rgba.brightness(shift_factor)
        return rgba.get_rgb()

    def get_tools(self, tools, use_annotation, use_wrapping):
        toolbar_options = {
            "gutter": TOOL_GUTTER,
            "print": TOOL_PRINT,
            "plain_text": TOOL_PLAIN_TEXT,
            "annotation": TOOL_ANNOTATION if use_annotation else "",
            "theme": TOOL_DUMP_THEME,
            "wrapping": TOOL_WRAPPING if use_wrapping else ""
        }
        t_opt = ""
        toolbar_element = ""

        if len(tools):
            for t in tools:
                if t in toolbar_options:
                    t_opt += toolbar_options[t]
            toolbar_element = TOOLBAR % {"options": t_opt}
        return toolbar_element

    def strip_transparency(self, color, track_darkness=False, simple_strip=False):
        if color is None:
            return color
        rgba = RGBA(color.replace(" ", ""))
        if not simple_strip:
            rgba.apply_alpha(self.bground if self.bground != "" else "#FFFFFF")
        if track_darkness:
            lumens = rgba.luminance()
            if self.dark_lumens is None or lumens < self.dark_lumens:
                self.dark_lumens = lumens
        return rgba.get_rgb()

    def setup_print_block(self, curr_sel, multi=False):
        # Determine start and end points and whether to parse whole file or selection
        if not multi and (curr_sel.empty() or self.highlight_selections or curr_sel.size() <= self.char_limit):
            self.size = self.view.size()
            self.pt = 0
            self.end = 1
            self.curr_row = 1
        else:
            self.size = curr_sel.end()
            self.pt = curr_sel.begin()
            self.end = self.pt + 1
            self.curr_row = self.view.rowcol(self.pt)[0] + 1
        self.start_line = self.curr_row

        self.gutter_pad = len(str(self.view.rowcol(self.size)[0])) + 1

    def check_sel(self):
        multi = False
        for sel in self.view.sel():
            if not sel.empty() and sel.size() >= self.char_limit:
                multi = True
                self.sels.append(sel)
        return multi

    def print_line(self, line, num):
        html_line = LINE % {
            "line_id": num,
            "color": self.gfground,
            "line": str(num).rjust(self.gutter_pad).replace(" ", '&nbsp;'),
            "code_id": num,
            "code": line,
            "table": self.tables,
            "pad_color": self.ebground or self.bground
        }

        return html_line

    def guess_colour(self, pt, the_key):
        the_colour = self.fground
        the_bgcolour = None
        the_style = set([])
        if the_key in self.matched:
            the_colour = self.matched[the_key]["color"]
            the_style = self.matched[the_key]["style"]
            the_bgcolour = self.matched[the_key]["bgcolor"]
        else:
            best_match_bg = 0
            best_match_fg = 0
            best_match_style = 0
            for key in self.colours:
                match = self.view.score_selector(pt, key)
                if self.colours[key]["color"] is not None and match > best_match_fg:
                    best_match_fg = match
                    the_colour = self.colours[key]["color"]
                if self.colours[key]["style"] is not None and match > best_match_style:
                    best_match_style = match
                    for s in self.colours[key]["style"]:
                        the_style.add(s)
                if self.colours[key]["bgcolor"] is not None and match > best_match_bg:
                    best_match_bg = match
                    the_bgcolour = self.colours[key]["bgcolor"]
            self.matched[the_key] = {"color": the_colour, "bgcolor": the_bgcolour, "style": the_style}
        if len(the_style) == 0:
            the_style = "normal"
        else:
            the_style = ' '.join(the_style)
        return the_colour, the_style, the_bgcolour

    def write_header(self, the_html):
        header = HTML_HEADER % {
            "title": path.basename(self.file_name),
            "css":   getcss(
                'export.css',
                {
                    "font_size":           str(self.font_size),
                    "font_face":           '"' + self.font_face + '"',
                    "page_bg":             self.bground,
                    "gutter_bg":           self.gbground,
                    "body_fg":             self.fground,
                    "display_mode":        'table-cell' if self.numbers else 'none',
                    "dot_color":           self.fground,
                    "toolbar_orientation": self.toolbar_orientation
                }
            ),
            "js": INCLUDE_THEME % {
                "jscode": getjs('plist.js'),
                "theme": json.dumps(self.plist_file, sort_keys=True, indent=4, separators=(',', ': ')).encode('raw_unicode_escape'),
                "name": self.scheme_file,
            }
        }
        the_html.write(header)

    def convert_view_to_html(self, the_html):
        for line in self.view.split_by_newlines(sublime.Region(self.pt, self.size)):
            self.size = line.end()
            empty = not bool(line.size())
            line = self.convert_line_to_html(the_html, empty)
            the_html.write(self.print_line(line, self.curr_row))
            self.curr_row += 1

    def html_encode(self, text):
        # Format text to HTML
        encode_table = {
            '&':  '&amp;',
            '>':  '&gt;',
            '<':  '&lt;',
            '\t': ' ' * self.tab_size,
            '\n': ''
        }

        return ''.join(encode_table.get(c, c) for c in text).encode('ascii', 'xmlcharrefreplace')

    def get_annotations(self):
        annotations = get_annotations(self.view)
        comments = []
        for x in range(0, int(annotations["count"])):
            region = annotations["annotations"]["html_annotation_%d" % x]["region"]
            comments.append((region, annotations["annotations"]["html_annotation_%d" % x]["comment"]))
        comments.sort()
        return comments

    def annotate_text(self, line, the_colour, the_bgcolour, the_style, empty):
        pre_text = None
        annot_text = None
        post_text = None
        start = None

        # Pretext Check
        if self.pt >= self.curr_annot.begin():
            # Region starts with an annotation
            start = self.pt
        else:
            # Region has text before annoation
            pre_text = self.html_encode(self.view.substr(sublime.Region(self.pt, self.curr_annot.begin())))
            start = self.curr_annot.begin()

        if self.end == self.curr_annot.end():
            # Region ends annotation
            annot_text = self.html_encode(self.view.substr(sublime.Region(start, self.end)))
            self.curr_annot = None
        elif self.end > self.curr_annot.end():
            # Region has text following annotation
            annot_text = self.html_encode(self.view.substr(sublime.Region(start, self.curr_annot.end())))
            post_text = self.html_encode(self.view.substr(sublime.Region(self.curr_annot.end(), self.end)))
            self.curr_annot = None
        else:
            # Region ends but annotation is not finished
            annot_text = self.html_encode(self.view.substr(sublime.Region(start, self.end)))
            self.curr_annot = sublime.Region(self.end, self.curr_annot.end())

        # Print the separate parts pre text, annotation, post text
        if pre_text != None:
            self.format_text(line, pre_text, the_colour, the_bgcolour, the_style, empty)
        if annot_text != None:
            self.format_text(line, annot_text, the_colour, the_bgcolour, the_style, empty, annotate=True)
            if self.curr_annot == None:
                self.curr_comment = None
        if post_text != None:
            self.format_text(line, post_text, the_colour, the_bgcolour, the_style, empty)

    def add_annotation_table_entry(self):
        row, col = self.view.rowcol(self.annot_pt)
        self.annot_tbl.append(
            (
                self.tables, self.curr_row, "Line %d Col %d" % (row + 1, col + 1),
                re.sub(r'(?!\s($|\S))\s', '&nbsp;', self.curr_comment.encode('ascii', 'xmlcharrefreplace').replace('\t', ' ' * self.tab_size))
            )
        )
        self.annot_pt = None

    def format_text(self, line, text, the_colour, the_bgcolour, the_style, empty, annotate=False):
        if empty:
            text = '&nbsp;'
        else:
            the_style += " real_text"

        if the_bgcolour is None:
            the_bgcolour = self.bground

        if annotate:
            code = ANNOTATION_CODE % {"highlight": the_bgcolour, "color": the_colour, "content": text, "class": the_style}
        else:
            code = CODE % {"highlight": the_bgcolour, "color": the_colour, "content": text, "class": the_style}

        if annotate:
            if self.curr_annot != None and not self.open_annot:
                # Open an annotation
                if self.annot_pt != None:
                    self.add_annotation_table_entry()
                if self.new_annot:
                    self.annot_num += 1
                    self.new_annot = False
                code = ANNOTATE_OPEN % {"code": code, "comment": str(self.annot_num)}
                self.open_annot = True
            elif self.curr_annot == None:
                if self.open_annot:
                    # Close an annotation
                    code += ANNOTATE_CLOSE
                    self.open_annot = False
                else:
                    # Do a complete annotation
                    if self.annot_pt != None:
                        self.add_annotation_table_entry()
                    if self.new_annot:
                        self.annot_num += 1
                        self.new_annot = False
                    code = (
                        ANNOTATE_OPEN % {"code": code, "comment": str(self.annot_num)} +
                        ANNOTATE_CLOSE
                    )
        line.append(code)

    def convert_line_to_html(self, the_html, empty):
        line = []
        hl_done = False

        # Continue highlight form last line
        if self.hl_continue != None:
            self.curr_hl = self.hl_continue
            self.hl_continue = None

        while self.end <= self.size:
            # Get next highlight region
            if self.highlight_selections and self.curr_hl == None and len(self.highlights) > 0:
                self.curr_hl = self.highlights.pop(0)

            # See if we are starting a highlight region
            if self.curr_hl != None and self.pt == self.curr_hl.begin():
                # Get text of like scope up to a highlight
                scope_name = self.view.scope_name(self.pt)
                while self.view.scope_name(self.end) == scope_name and self.end < self.size:
                    # Kick out if we hit a highlight region
                    if self.end == self.curr_hl.end():
                        break
                    self.end += 1
                if self.end < self.curr_hl.end():
                    if self.end >= self.size:
                        self.hl_continue = sublime.Region(self.end, self.curr_hl.end())
                    else:
                        self.curr_hl = sublime.Region(self.end, self.curr_hl.end())
                else:
                    hl_done = True
                if hl_done and empty:
                    the_colour, the_style, the_bgcolour = self.guess_colour(self.pt, scope_name)
                elif self.sfground is None:
                    the_colour, the_style, _ = self.guess_colour(self.pt, scope_name)
                    the_bgcolour = self.sbground
                else:
                    the_colour, the_style = self.sfground, "normal"
                    the_bgcolour = self.sbground
            else:
                # Get text of like scope up to a highlight
                scope_name = self.view.scope_name(self.pt)
                while self.view.scope_name(self.end) == scope_name and self.end < self.size:
                    # Kick out if we hit a highlight region
                    if self.curr_hl != None and self.end == self.curr_hl.begin():
                        break
                    self.end += 1
                the_colour, the_style, the_bgcolour = self.guess_colour(self.pt, scope_name)

            # Get new annotation
            if (self.curr_annot == None or self.curr_annot.end() < self.pt) and len(self.annotations):
                self.curr_annot, self.curr_comment = self.annotations.pop(0)
                self.annot_pt = self.curr_annot[0]
                while self.pt > self.curr_annot[1]:
                    if len(self.annotations):
                        self.curr_annot, self.curr_comment = self.annotations.pop(0)
                        self.annot_pt = self.curr_annot[0]
                    else:
                        self.curr_annot = None
                        self.curr_comment = None
                        break
                self.new_annot = True
                self.curr_annot = sublime.Region(self.curr_annot[0], self.curr_annot[1])

            region = sublime.Region(self.pt, self.end)
            if self.curr_annot != None and region.intersects(self.curr_annot):
                # Apply annotation within the text and format the text
                self.annotate_text(line, the_colour, the_bgcolour, the_style, empty)
            else:
                # Normal text formatting
                tidied_text_1 = self.html_encode(self.view.substr(region))
                tidied_text = re.sub(r'(?!\s($|\S))\s', '&nbsp;', tidied_text_1)
                self.format_text(line, tidied_text, the_colour, the_bgcolour, the_style, empty)

            if hl_done:
                # Clear highlight flags and variables
                hl_done = False
                self.curr_hl = None

            # Continue walking through line
            self.pt = self.end
            self.end = self.pt + 1

        # Close annotation if open at end of line
        if self.open_annot:
            line.append(ANNOTATE_CLOSE % {"comment": self.curr_comment})
            self.open_annot = False

        # Get the color for the space at the end of a line
        if self.end < self.view.size():
            end_key = self.view.scope_name(self.pt)
            _, _, self.ebground = self.guess_colour(self.pt, end_key)

        # Join line segments
        return ''.join(line)

    def write_body(self, the_html):
        processed_rows = ""
        the_html.write(BODY_START)

        the_html.write(TABLE_START)
        if not self.no_header:
            # Write file name
            date_time = time.strftime(self.date_time_format, self.time)
            the_html.write(
                FILE_INFO % {
                    "color": self.fground,
                    "date_time": date_time,
                    "file": self.file_name if self.show_full_path else path.basename(self.file_name)
                }
            )

        the_html.write(ROW_START)
        the_html.write(TABLE_START)
        # Convert view to HTML
        if self.multi_select:
            count = 0
            total = len(self.sels)
            for sel in self.sels:
                self.setup_print_block(sel, multi=True)
                processed_rows += "[" + str(self.curr_row) + ","
                self.convert_view_to_html(the_html)
                count += 1
                self.tables = count
                processed_rows += str(self.curr_row) + "],"

                if count < total:
                    the_html.write(TABLE_END)
                    the_html.write(ROW_END)
                    the_html.write(ROW_START)
                    the_html.write(DIVIDER % {"color": self.fground})
                    the_html.write(ROW_END)
                    the_html.write(ROW_START)
                    the_html.write(TABLE_START)
        else:
            self.setup_print_block(self.view.sel()[0])
            processed_rows += "[" + str(self.curr_row) + ","
            self.convert_view_to_html(the_html)
            processed_rows += str(self.curr_row) + "],"
            self.tables += 1

        the_html.write(TABLE_END)
        the_html.write(ROW_END)
        the_html.write(TABLE_END)

        js_options = []
        if len(self.annot_tbl):
            self.add_comments_table(the_html)
            js_options.append(HTML_JS_WRAP % {"jscode": getjs('annotation.js')})

        # Write javascript snippets
        js_options.append(HTML_JS_WRAP % {"jscode": getjs('print.js')})
        js_options.append(HTML_JS_WRAP % {"jscode": getjs('plaintext.js')})
        js_options.append(TOGGLE_LINE_OPTIONS % {
                "jscode":    getjs('lines.js'),
                "wrap_size": self.wrap,
                "ranges":    processed_rows.rstrip(','),
                "tables":    self.tables,
                "header":    ("false" if self.no_header else "true"),
                "gutter":    ('true' if self.numbers else 'false')
            }
        )
        if self.auto_wrap:
            js_options.append(WRAP)

        if self.browser_print:
            js_options.append(AUTO_PRINT)

        # Write empty line to allow copying of last line and line number without issue
        the_html.write(BODY_END % {"js": ''.join(js_options), "toolbar": self.get_tools(self.toolbar, len(self.annot_tbl), self.auto_wrap)})

    def add_comments_table(self, the_html):
        the_html.write(ANNOTATION_TBL_START)
        the_html.write(''.join([ANNOTATION_ROW % {"table": t, "row": r, "link": l, "comment": c} for t, r, l, c in self.annot_tbl]))
        the_html.write(ANNOTATION_FOOTER)
        the_html.write(ANNOTATION_TBL_END)

    def run(self, **kwargs):
        inputs = self.process_inputs(**kwargs)
        self.setup(**inputs)

        save_location = inputs["save_location"]
        time_stamp = inputs["time_stamp"]

        if save_location is not None:
            fname = self.view.file_name()
            if (
                ((fname == None or not path.exists(fname)) and save_location == ".") or
                not path.exists(save_location)
                or not path.isdir(save_location)
            ):
                html_file = ".html"
                save_location = None
            elif save_location == ".":
                html_file = "%s%s.html" % (fname, time.strftime(time_stamp, self.time))
            elif fname is None or not path.exists(fname):
                html_file = path.join(save_location, "Untitled%s.html" % time.strftime(time_stamp, self.time))
            else:
                html_file = path.join(save_location, "%s%s.html" % (path.basename(fname), time.strftime(time_stamp, self.time)))
        else:
            html_file = ".html"

        if save_location is not None:
            open_html = lambda x: open(x, "w")
        else:
            open_html = lambda x: tempfile.NamedTemporaryFile(delete=False, suffix=x)

        with open_html(html_file) as the_html:
            self.write_header(the_html)
            self.write_body(the_html)
            if inputs["clipboard_copy"]:
                the_html.seek(0)
                sublime.set_clipboard(the_html.read())
                sublime.status_message("Export to HTML: copied to clipboard")

        if inputs["view_open"]:
            self.view.window().open_file(the_html.name)
        else:
            # Open in web browser; check return code, if failed try webbrowser
            status = desktop.open(the_html.name, status=True)
            if not status:
                webbrowser.open(the_html.name, new=2)
