# ExportHtml

## 2.15.0

- **NEW**: Support `lightness()` and `saturation()` in color mod functions.
- **NEW**: Properly support `alpha(+value)`, `alpha(-value)`, `alpha(*value)`, and `alpha(value)`.
- **NEW**: Suppport `foreground_adjust`.

## 2.14.4

- **FIX**: Fix references to internal color schemes in settings. Color schemes wouldn't load proper as the color scheme
  names were wrong.

## 2.14.3

- **FIX**: Mimic Sublime in regards to hue blending.

## 2.14.2

- **FIX**: Fix `HWB` exception.

## 2.14.1

- **FIX**: Fix some regressions in regard to blending colors.
- **FIX**: Fix issue where `HWB` blending was used when it shouldn't be.

## 2.14.0

- **NEW**: Respect `no_bold` and `no_italic` options in `font_options`.
- **NEW**: Default themes converted to `sublime-color-scheme` format.
- **NEW**: Handle blending in `HSL` and `HWB` color space.
- **FIX**: Improved color blending.

## 2.13.0

- **NEW**: Add support for `hwb()` and `alpha()`/`a()`.
- **FIX**: Handle `hsl()` in `blend()`.

## 2.12.1

- **FIX**: Allow `-` in variables names. Write color translations to main scheme object and ensure filtering is done after color translations.

## 2.12.0

- **NEW**: Better tab conversion algorithm. Converts tabs to spaces based on tab stops (though it doesn't account for character width).
- **NEW**: Using `disable_nbsp` will insert real tabs or spaces.
- **NEW**: Settings are gathered from the view under conversion, not the global preferences.
- **NEW**: Default provided print setups now disables `nbsp` by default to use the exact whitespace in a file.
- **FIX**: Font in HTML not being displayed correctly.

## 2.11.0

- **NEW**: Add support for `.hidden-color-scheme`.
- **FIX**: Update dependencies.

## 2.10.2

- **FIX**: Create fallback file read for resource race condition.

## 2.10.1

- **FIX**: Parse legacy `foregroundSelection` properly.

## 2.10.0

- **NEW**: Add support `.sublime-color-scheme` hashed syntax highlighting.
- **FIX**: `.sublime-color-scheme` merge logic.

## 2.9.1

- **FIX**: Parse color scheme with unexpected extension correctly.

## 2.9.0

- **NEW**: Add support for rendering output without tables (Default CSS did change, so if overriding it, you may need to update).
- **FIX**: Support for irregular `.sublime-color-scheme` values.

## 2.8.0

- **NEW**: Add support for per scope selection foreground.
- **FIX**: Some general color scheme parsing and tweaking issues.

## 2.7.0

- **NEW**: Add support for `.sublime-color-scheme` files.
- **NEW**: Drop option to include scheme in output.

## 2.6.0

- **NEW**: Upgrade theme_tweaker and rgba lib which adds the ability to adjust contrast.
- **FIX**: Don't include document build folder.

## 2.5.0

- **NEW**: Add document and settings to the command palette.
- **FIX**: Quick start image links.

## 2.4.1

- **FIX**: Hopefully more reliable browser opening (#47).

## 2.4.0

- **NEW**: Limit popups to 3124+.
- **FIX**: Better scope matching.

## 2.3.1

- **FIX**: Skip processing popupCss and phantomCss.

## 2.3.0

- **NEW**: Handle X11 named colors in color schemes (#44).
- **NEW**: By default, don't include color scheme plist in output (to reduce size of output).
- **NEW**: Quickstart guide available in menu.
- **NEW**: Links to repo issues and documentation available in menu.

## 2.2.2

- **FIX**: Fix changelog links

## 2.2.1

- **Fix**: Fix incorrect changelog title (#43).

## 2.2.0

- **NEW**: Add `disable_nbsp` option.
- **Fix**: JS not loading into HTML.

## 2.1.0

- **NEW**: New dependencies.
- **NEW**: Added changelog and support info command in menu.
- **NEW**: CSS template is now handled by Jinja2.
- **NEW**: Add `export_css` setting to specify custom CSS.

## 2.0.0

- **NEW**: Arbitrary jump to 2.0.0 version number
- **NEW**: Upgrade color libs
- **NEW**: Get current scheme from view settings instead of global
