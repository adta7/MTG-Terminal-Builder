# Rich Reference

Quick reference for the `rich` Python library. Run `python -m rich` anytime to see a live demo in your terminal.

Official docs: https://rich.readthedocs.io/en/stable/

---

## Setup

```python
from rich.console import Console
console = Console()
```

---

## Colors

Rich auto-detects your terminal's color support and converts accordingly.

| Level         | Example                                      |
|---------------|----------------------------------------------|
| 4-bit (basic) | `red`, `green`, `blue`, `magenta`, `cyan`     |
| 8-bit         | `color(0)` to `color(255)`                   |
| Truecolor     | `#af00ff` or `rgb(175,0,255)`                |
| Background    | `red on white`                               |

```python
console.print("[red]Red[/red]")
console.print("[#af00ff]Hex color[/#af00ff]")
console.print("[rgb(175,0,255)]RGB color[/rgb(175,0,255)]")
console.print("[red on white]Red on white background[/red on white]")
```

---

## Styles

All standard ANSI styles are supported:

```python
console.print("[bold]Bold[/bold]")
console.print("[dim]Dim[/dim]")
console.print("[italic]Italic[/italic]")
console.print("[underline]Underline[/underline]")
console.print("[strikethrough]Strikethrough[/strikethrough]")
console.print("[reverse]Reversed colors[/reverse]")
console.print("[blink]Blinking[/blink]")

# Combine freely
console.print("[bold red underline]Bold red underlined[/bold red underline]")
```

Shorthand closing tag `[/]` closes the most recent open tag:
```python
console.print("[bold red]Bold and red[/] back to normal")
```

---

## Text Alignment

```python
from rich.text import Text
from rich.console import Console

console = Console()

# Justify options: "left", "center", "right", "full"
console.print("Left aligned", justify="left")
console.print("Centered", justify="center")
console.print("Right aligned", justify="right")
```

---

## Markup

Rich uses bbcode-style square bracket markup:

```python
console.print("[bold]Bold[/bold]")
console.print("[italic cyan]Italic cyan[/italic cyan]")
console.print("[link=https://example.com]Click me[/link]")

# Emoji via shortcode
console.print(":warning: Warning!")
console.print(":red_heart: Love")

# Escape literal brackets (don't treat as markup)
console.print(r"\[not markup\]")
```

---

## Panels

Draws a border around content. Good for framing sections.

```python
from rich.panel import Panel
from rich import box

# Basic
console.print(Panel("Hello, [red]World!"))

# Fit to content width (don't expand to full terminal)
console.print(Panel.fit("Hello, World!"))

# With title, subtitle, and box style
console.print(Panel(
    "Content here",
    title="[bold cyan]Title[/bold cyan]",
    subtitle="subtitle",
    box=box.DOUBLE,
    style="cyan",
    padding=(1, 2),
    expand=False,
))
```

**Box styles** (import from `rich.box`):
`SIMPLE`, `MINIMAL`, `ROUNDED`, `HEAVY`, `DOUBLE`, `ASCII`, `SQUARE`, `MARKDOWN`

---

## Tables

```python
from rich.table import Table

table = Table(title="My Table", show_header=True, header_style="bold magenta")
table.add_column("Name", style="cyan", justify="left")
table.add_column("Value", justify="right")
table.add_row("Lightning Bolt", "{R}")
table.add_row("Counterspell", "{U}{U}")
console.print(table)
```

**Column options** (set in `add_column()`):
- `justify` — `"left"`, `"center"`, `"right"`, `"full"`
- `style` — any Rich style string
- `width`, `min_width`, `max_width`
- `no_wrap` — prevent text wrapping

**Table options:**
- `box=box.SIMPLE` — change border style
- `show_header=False` — hide header row
- `show_lines=True` — show row dividers
- `expand=True` — stretch to terminal width

---

## Progress Bars

Simple one-liner for loops:

```python
from rich.progress import track

for item in track(my_list, description="Processing..."):
    do_work(item)
```

Full control with context manager:

```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("[cyan]Loading...", total=len(items))
    for item in items:
        do_work(item)
        progress.advance(task)
```

**Column types** for custom progress display:
`BarColumn`, `SpinnerColumn`, `TimeElapsedColumn`, `TimeRemainingColumn`, `TextColumn`

---

## Syntax Highlighting

```python
from rich.syntax import Syntax

code = '''def hello():
    print("Hello, world!")'''

syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
console.print(syntax)
```

---

## Markdown

```python
from rich.markdown import Markdown

md = Markdown("# Title\n\nSome **bold** and *italic* text.\n\n- Item 1\n- Item 2")
console.print(md)
```

---

## Themes (reusable styles)

```python
from rich.theme import Theme

theme = Theme({
    "info":    "dim cyan",
    "warning": "bold yellow",
    "error":   "bold red",
    "success": "bold green",
})
console = Console(theme=theme)

console.print("All good", style="success")
console.print("Watch out", style="warning")
console.print("Something broke", style="error")
```

---

## Useful Console Options

```python
# Force a specific width (useful for testing)
console = Console(width=80)

# Write to stderr instead of stdout
err_console = Console(stderr=True)

# Strip all markup (plain text output)
plain = Console(highlight=False, markup=False)
```

---

## Quick Cheatsheet

| Goal                        | Code                                          |
|-----------------------------|-----------------------------------------------|
| Bold red text               | `[bold red]text[/bold red]`                   |
| Dim/muted text              | `[dim]text[/dim]`                             |
| Inline color                | `[cyan]text[/cyan]`                           |
| Close last tag              | `[/]`                                         |
| Emoji                       | `:fire:` `:warning:` `:check_mark:`           |
| Draw a box                  | `Panel("content", title="Title")`             |
| Table                       | `Table()` + `add_column()` + `add_row()`      |
| Progress loop               | `for x in track(items, description="..."):`   |
| Markdown                    | `console.print(Markdown("# Hello"))`          |
| Syntax highlight            | `console.print(Syntax(code, "python"))`       |
| Get terminal width          | `Console().width` or `shutil.get_terminal_size().columns` |
