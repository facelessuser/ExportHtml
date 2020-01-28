# User Guide

## Exporting HTML

ExportHtml comes with a number of default commands available, but these can be overridden in the settings file.  You can also create commands directly outside of the settings file bound to the command palette, key bindings, or even the menu.

If adding a command to the settings file, it goes under the `html_panel` setting.  These configurations will appear under the `Export to HTML: Show Export Menu` command palette command.

```javascript
// Define configurations for the drop down export menu
"html_panel": [
    // Browser print color (selections and multi-selections allowed)
    {
        "Browser Print - Color": {
            "numbers": true,
            "wrap": 900,
            "browser_print": true,
            "multi_select": true,
            "color_scheme": "Packages/ExportHtml/ColorSchemes/Print Color.sublime-color-scheme",
            "style_gutter": false
        }
    }
 ]
```

The name of the command is the key value, and then you add the parameters you wish to specify.  You can use any combination of settings below.

Parameter              | Type               | Description
---------------------- | ------------------ | -----------
`numbers`              | boolean            | Display line numbers in the gutter.
`style_gutter`         | boolean            | Style gutter with theme backgrounds and foregrounds, or just use the default background/foreground.  Default is `true`.
`multi_select`         | boolean            | If multiple regions are selected in a document, only export what is under those selections. By default only the first selection is recognized.  Default is `false`.
`highlight_selections` | boolean            | Highlights all selections in HTML output using the themes selection colors.  Multi-select option will be ignored if this is set `true`.  Default is `false`.
`ignore_selections`    | boolean            | Ignores selections in the view.  If this is set, `multi_select` and `highlight_selections` will be treated as `false` regardless of their actual value.
`wrap`                 | integer            | Define the allowable size in `px` to wrap lines at.  By default wrapping is not used.
`color_scheme`         | string             | The color scheme (tmTheme or sublime-color-scheme) file you would like to use.  By default the current color scheme file is used, or the alternate default color scheme if defined in the setting `alternate_scheme`.
`clipboard_copy`       | boolean            | Copy HTML to the clipboard after generation. Default is `false`.
`browser_print`        | boolean            | When opening in the web browser, also open the browser's print dialog. This will be ignored if `view_open` is `true`.  Default is `false`.
`view_open`            | boolean            | Open HTML in a Sublime Text tab instead of the web browser.  Default is `false`.
`no_header`            | boolean            | Do not display file name, date, and time at the top of the HTML document. Default is `false`.
`date_time_format`     | string             | String denoting the format for date and time when displaying header.  Please see Python's documentation on `time.strftime` for detailed info on formatting syntax.  Default is `"%m/%d/%y %I:%M:%S"`.
`show_full_path`       | boolean            | Show full path for file name when displaying header. Default is `true`.
`save_location`        | string             | Path to save HTML file.  If the file is wanted in the same file as the original, use ".".  Otherwise, use the absolute path to where the file is desired.  If there is an issue determining where to save the file, or the path does not exist, the OS temp folder will be used. Default is `None` (use temp folder).
`time_stamp`           | string             | Configure the time stamp of saved HTML when using `save_location`.  To remove time stamps, just set to an empty string `""`.  Please see Python's documentation on `time.strftime` for detailed info on formatting syntax.  Default is `"_%m%d%y%H%M%S"`.
`toolbar`              | array\ of\ strings | Option to display a toolbar with to access features in a generated HTML.  This setting is an array of keywords that represent the icons in the toolbar to show.  Valid keywords include `gutter`, `print`, `plain_text`, `annotation`, and `wrapping`.  Toolbar will appear when you mouse over the upper right corner of the window of the generated HTML.  Default enables all.
`filter`               | string             | Filters to use on the theme's colors.  The string is a sequence of filters separated by `;`.  The accepted filters are `grayscale`, `invert`, `sepia`, `brightness`, `contrast`, `glow`, `saturation`, `hue`, and `colorize`.  `brightness`, `saturation`, and `contrast` require a float parameter to specify to what magnitude the filter should be applied at.  `glow` requires a float for intensity (usually something like .1 or .2 is sufficient).  `hue` and `colorize` take a float that represents a degree.  `hue` shifts the hue via the degree given (can accept negative degrees); hues will wrap if they extend past 0 degrees or 360 degrees.  Example: `"filter": "sepia;invert;brightness(1.1);saturation(1.3);"`.  Default is `""`.
`disable_nbsp`         | boolean            | Disable the translation of spaces into `&nbsp;`.  This was originally introduced so I could copy and paste content into Microsoft Outlook.  If this is not desired, you can disable it here.
`table_mode`           | boolean            | Render export of code in tables which makes copy and paste in things like Outlook or Gmail possible. Default is `true`.

If you wish to bind a command to a key combination etc., the same settings as above can be used.

Example:

```js
{
    "keys": ["ctrl+alt+n"],
    "command": "export_html",
    "args": {
        "numbers": true,
        "wrap": 900,
        "browser_print": true,
        "multi_select": true,
        "color_scheme": "Packages/ExportHtml/ColorSchemes/Print Color.sublime-color-scheme",
        "style_gutter": false
    }
}
```

When viewing the HTML in your web browser, regardless of the gutter settings, the gutter can be toggled to show or be hidden using the toolbar in the upper right corner of the page.

## Exporting BBCode

ExportHtml can also export selected code as BBCode for posting in forums. Exporting BBCode is very similar to exporting HTML code.  But keep in mind, not all forums have all the BBCode support needed to view ExportHtml's BBCode format, so your mileage may vary.

If adding a command to the settings file, it goes under the `bbcode_panel` setting.  These configurations will appear under the `Export to BBCode: Show Export Menu` command palette command.

```js
// Define configurations for the drop down export menu
"bbcode_panel": [
    {
        "To Clipboard - Format as BBCode": {
            "numbers": false,
            "multi_select": true
        }
    }
]
```

The name of the command is the key value, and then you add the parameters you wish to specify.  You can use any combination of settings below.

Parameter           | Type    | Description
------------------- | ------- | -----------
`numbers`           | boolean | Display line numbers in the gutter.
`multi_select`      | boolean | If multiple regions are selected in a document, only export what is under those selections. By default only the first selection is recognized.  Default is `false`.
`ignore_selections` | boolean | Ignores selections in the view.  If this is set, `multi_select` will be treated as `false` regardless of its actual value.
`color_scheme`      | string  | The color scheme (tmTheme) file you would like to use.  By default the current color scheme file is used, or the the alternate default color scheme if defined in the setting `alternate_scheme`.
`clipboard_copy`    | boolean | Copy BBCode to the clipboard after generation. Default is `true`.
`view_open`         | boolean | Open text file of BBCode in a Sublime Text tab.  Default is `false`.
`no_header`         | boolean | Do not display file name, date, and time at the top of the HTML document. Default is `false`.

If you wish to bind a command to a key combination etc., the same settings as above can be used.

Example:

```js
{
    "keys": ["ctrl+alt+n"],
    "command": "export_bbcode",
    "args": {
        "numbers": false,
        "multi_select": true
    }
}
```

## Annotations (HTML only)

Annotations are comments you can make on selected text.  When the HTML is generated, the selected text will be underlined, and when the mouse hovers over them, a tooltip will appear with your comment.

![annotation_preview](images/annotation_preview.png)

In order to use annotations, you must enter into an "Annotation Mode".  This puts your file in a read only state.  At this point, you can select text and create annotations using the annotation commands provided.  When you leave the "Annotation Mode", all annotations will be lost.  So you must export before leaving annotation mode.

You can access the annotation commands from the command palette or from the context menu.

The commands are as follows:

Command                 | Description
----------------------- | -----------
Enable Annotation Mode  | Turn annotation mode on.
Disable Annotation Mode | Turn annotation mode off.
Annotate Selection      | Annotate the given selection (no multi-select support currently).
Delete Annotation(s)    | Delete the annotation region the the cursor resides in (multi-select support).
Delete All Annotations  | Delete all annotation regions.
Show Annotation Comment | Show the annotation comment of the region under the cursor.

You can navigate the annotations in the generated HTML by using a jump table.  You can show the jump table at any time by selecting the annotation button in the toolbar.  You can also click any annotation to show the jump table as well.  If it gets in the way, you can dock it in a different location.

![annotation_table_preview](images/annotation_table_preview.png)

## Settings File options

Parameter              | Type                | Description
---------------------- | ------------------- | -----------
`alternate_scheme`     | string\ or\ false   | Defines a default theme to be used if a theme is not specified in a command.  When this is false, the current Sublime Text theme in use is used.
`alternate_font_size`  | integer\ or\ false  | Define an alternate font_size to use by default instead of the current one in use.  Use the current one in use if set to a literal `false`.  Default is `false`.
`alternate_font_face`  | string\ or\ false   | Define an alternate font_face to use by default instead of the current one in use.  Use the current one in use if set to a literal `false`.  Default is `false`.
`valid_selection_size` | integer             | Minimum allowable size for a selection to be accepted for only the selection to be printed.
`html_panel`           | array\ of\ commands | Define export configurations to appear under the `Export to HTML: Show Export Menu` command palette command.
`bbcode_panel`         | array\ of\ commands | Define export configurations to appear under the `Export to BBCode: Show Export Menu` command palette command.

--8<-- "refs.md"
