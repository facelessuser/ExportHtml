# Getting Started

![preview](res://Packages/ExportHtml/docs/src/markdown/images/preview.png){: width=628px, height=559px}

ExportHtml is a plugin that can take a Sublime Text view (or selection(s) within a view) and generate a HTML output that  
reproduces the entire selection (text, colors, etc.) and opens the HTML document in your web browser, copies the content  
to the clipboard, or opens a new Sublime Text view with the HTML content.

ExportHtml has a BBCode option as well to generate a BBCode output for forums that have enabled all the required features.  
The BBCode variant will not open in an external browser, but it will copy the content to the clipboard or open a new  
Sublime Text view with the BBCode content.

To get started, you can run the command `Export to HTML: Show Export Menu` and select an option from the default entries.  
These entries are defined in the [settings file](sub://Packages/ExportHtml/ExportHtml.sublime-settings).

HTML outputs have a toolbar in the upper right hand corner which should appear on hover.  You can do things like hide  
line numbers, see a plain text output, initiate a print, etc.  It all depends on what the command has enabled.

![toolbar](res://Packages/ExportHtml/docs/src/markdown/images/toolbar.png){: width=137, height=53}

To create your own list of export options, check out the [documentation](http://facelessuser.github.io/ExportHtml/usage/#exporting-html).

# Annotations

![preview](res://Packages/ExportHtml/docs/src/markdown/images/annotation_preview.png){: width=737px, height=295px}

Annotations was just a fun idea.  Not sure how useful it is in practice, but you can enable annotation mode and select  
words or phrases and add annotations.  On HTML export, the targeted words and phrases will be underlined and on mouseover  
a tooltip with your annotation will be visible.  To learn more read about annotations in the [documentation](http://facelessuser.github.io/ExportHtml/usage/#annotations-html-only).

# I Want To Use This For Printing

Some people use ExportHtml for this printing. Out of the box, ExportHtml provides two export options for this purpose:

- Browser Print - Color (Selection Highlights)
- Browser Print - Grayscale (Selection Highlights)

These will generate your code with special color schemes with pure white backgrounds for printing.  The content will be  
opened in your web browser. It will inject JavaScript into the output which will trigger the browser to open the print  
dialog.

If you want a print entry in the menu, you can add something like this in `Main.sublime-menu` in your user folder:

```js
    {
        "id": "file",
        "children":
        [
            { "caption": "-" },
            {
                "command": "export_html",
                "args": {
                    "numbers": true,
                    "wrap": 900,
                    "browser_print": true,
                    "multi_select": true,
                    "color_scheme": "Packages/ExportHtml/ColorSchemes/Print-Grayscale.tmTheme",
                    "style_gutter": false
                },
                "caption": "Print (Export HTML)"
            },
            { "caption": "-" }
        ]
    },
```

# Why is the HTML Content Wrapped in a Table?

My interest in creating this plugin was to generate an HTML variant of a snippet of code that I could easily copy and paste  
into emails.  Though people use it to print and various other use cases, that was originally why I wrote this. Tables  
were needed in order for me to create an HTML output that copied well into emails. In the future, this may or may not  
become optional.

# I Need Help!

That's okay.  Bugs are sometimes introduced or discovered in existing code.  Sometimes the documentation isn't clear.  
Support can be found over on the [official repo](https://github.com/facelessuser/ColorHelper/issues).  Make sure to first search the documentation and previous issues  
before opening a new issue.  And when creating a new issue, make sure to fill in the provided issue template.  Please  
be courteous and kind in your interactions.
