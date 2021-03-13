# ExportHtml

## Overview

This is a fork of [Andrew Gibson][gibson]'s [PrintHtml][print-html] plugin.  This plugin allows the exporting of a
document in Sublime Text to a HTML file.  It duplicates Sublime's theme colors and font styles.

![preview](images/preview.png)

## Features

- Export to HTML using any `tmTheme` or `sublime-color-scheme` for syntax highlighting.
- Can handle any language supported by ST3+.
- Supports bold and italic theme font styles as well.
- Configurable output.
- Format suitable for copying and pasting in emails.
- 2 included `sublime-color-scheme` files for color and grayscale printing (but any can be used).
- Export only selections (multi-select supported).
- Export and show highlights (multi-select supported).
- Toggle gutter on/off in browser view.
- Automatically open browser print dialog (optional).
- Enable/disable configurable word wrapping.
- Configurable toolbar to appear in the generated webpage.

## Credits

- [Andrew Gibson][gibson]: Original idea and base code for converting Sublime view to HTML and allowing me to build off
  it to make ExportHtml.
- Print-Color and Print-Grayscale `sublime-color-scheme` files were derived from Monokai Bright.

--8<-- "refs.md"
