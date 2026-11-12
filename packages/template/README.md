# template

HTML template engine for Spice with a Jinja-like syntax: template inheritance, includes, macros with `caller()`,
imports, loops with `loop.*`, a full expression language, 50+ filters, tests, automatic HTML escaping, whitespace
control and error messages with template name and line. Pure Spice, no system libraries needed.

## Installation

```toml
[dependencies]
template = "^0.1.0"
```

```spice
import "spice_packages/template/template";
```

## Quick start

```spice
import "spice_packages/template/template";

f<int> main() {
    TemplateEngine engine;
    engine.add("base.html", "<title>{% block title %}My site{% endblock %}</title>{% block content %}{% endblock %}");
    engine.add("users.html", "{% extends \"base.html\" %}" +
        String("{% block title %}Users - {{ super() }}{% endblock %}") +
        "{% block content %}<ul>{% for user in users if user.active %}" +
        "<li class=\"{{ loop.cycle('odd', 'even') }}\">{{ user.name|title }}</li>" +
        "{% else %}<li>Nobody here</li>{% endfor %}</ul>{% endblock %}");

    TemplateValue ann;
    ann.set("name", "ann <admin>");
    ann.set("active", true);
    TemplateValue users;
    users.push(ann);
    TemplateValue data;
    data.set("users", users);

    Result<String> html = engine.render("users.html", data);
    if !html.isOk() {
        printf("%s\n", engine.lastError.getRaw()); // e.g. "users.html:1: unknown filter 'titel'"
        return 1;
    }
    printf("%s\n", html.unwrap().getRaw());
    // <title>Users - My site</title><ul><li class="odd">Ann &lt;Admin&gt;</li></ul>
}
```

Templates usually live in files:

```spice
TemplateEngine engine;
engine.trimBlocks = true;   // whitespace options apply to templates added afterwards
engine.lstripBlocks = true;
if !engine.loadDirectory("templates") {       // all *.html below the directory, named "partials/card.html" etc.
    printf("%s\n", engine.lastError.getRaw());
}
const String problems = engine.check();     // compile errors and references to missing templates, "" if fine
```

## Data

Templates read a `TemplateValue`: undefined, null, bool, int, float, string, list or map (keys keep their insertion
order). Copying a value copies the whole tree.

```spice
TemplateValue page;                            // undefined, becomes a map with the first set()
page.set("title", "Tea & Cake");               // string, long, int, double, bool or TemplateValue
page.set("intro", templateSafe("<em>new</em>")); // trusted markup, not escaped
TemplateValue tags = templateList();
tags.push("green");
page.set("tags", tags);

Result<TemplateValue> parsed = templateJson("{\"posts\": [{\"title\": \"Hello\"}]}");
```

| Method                                                | Purpose                                                    |
|-------------------------------------------------------|------------------------------------------------------------|
| `TemplateValue(x)`                                    | From `bool`, `int`, `long`, `double`, `string` or `String` |
| `templateList()`, `templateMap()`, `templateNull()`   | Empty list, empty map, null                                |
| `templateSafe(html)`                                  | A string that is output without escaping                   |
| `templateJson(json)`                                  | Parse JSON (`Result`, error if it is invalid)              |
| `set(key, value)`, `remove(key)`, `push(value)`       | Build maps and lists                                       |
| `get(key)`, `at(index)`, `has(key)`, `size()`         | Read (missing entries are undefined)                       |
| `isUndefined()`, `isNull()`, `isString()`, `isMap()`… | Kind checks                                                |
| `truthy()`, `asLong()`, `asDouble()`, `toString()`    | Conversions                                                |
| `toJson()`                                            | Serialize                                                  |

## Engine

| Method / field                         | Purpose                                                                       |
|----------------------------------------|-------------------------------------------------------------------------------|
| `add(name, source)`                    | Add or replace a template; `false` if it has errors (see `lastError`)          |
| `addFile(name, path)`                  | Add a template from a file                                                    |
| `loadDirectory(path, ext = ".html")`   | Add every file below a directory, named by its relative path                  |
| `render(name, data)`                   | Render to a `Result<String>`; on failure `lastError` says what and where      |
| `renderString(source, data)`           | Render a one-off source that can include, import and extend added templates  |
| `check()`                              | Report of all compile errors and unknown include/import/extends targets       |
| `addFilter(name, fn)`                  | Custom filter `f<TemplateValue>(const TemplateValue& value, const TemplateArgs& args)` |
| `addFunction(name, fn)`                | Custom function `f<TemplateValue>(const TemplateArgs& args)`                   |
| `addGlobal(name, value)`               | A variable every template sees (render data takes precedence)                 |
| `has(name)`, `names()`                 | Look up templates                                                             |
| `autoescape`                           | Escape `{{ }}` output for HTML (default `true`)                                |
| `strictUndefined`                      | Outputting, looping over or reading attributes of undefined values is an error |
| `trimBlocks`, `lstripBlocks`           | Jinja whitespace options                                                       |
| `stripIndentation`                     | Drop whitespace with line breaks between markup, for compact HTML              |
| `maxDepth`                             | Limit for nested includes, macro calls and inheritance (default 64)            |
| `lastError`                            | `name:line: message` of the last failure                                       |

`templateRender(source, data)` renders a single source with default settings, and `templateEscape(text)` escapes text
for HTML.

Custom filters and functions get their arguments as `TemplateArgs`: `args.get(index, "name")` returns the positional
argument at `index` or the keyword argument `name` (undefined if neither is given), `args.at(i)`, `args.byName(n)` and
`args.count()` are also available. Lambdas may capture variables:

```spice
const String currency = String("EUR");
engine.addFilter("price", f<TemplateValue>(const TemplateValue& v, const TemplateArgs& args) {
    const TemplateValue decimals = args.get(0l, "decimals");
    const int places = decimals.isUndefined() ? 2 : cast<int>(decimals.asLong());
    TemplateValue amount = TemplateValue(v.asDouble());
    // ... format as you like
    return TemplateValue(amount.toString() + " " + currency);
});
// {{ item.cost|price }}  {{ item.cost|price(decimals=0) }}
```

## Template syntax

```
{{ expression }}          output, HTML-escaped
{{{ expression }}}        output without escaping (same as |safe)
{% statement %}           control flow
{# comment #}             ignored
{%- ... -%} {{- ... -}}   strip the whitespace before / after the tag
```

### Expressions

| Kind          | Syntax                                                                                     |
|---------------|--------------------------------------------------------------------------------------------|
| Literals      | `"text"`, `'text'`, `42`, `1.5`, `true`/`false`, `none`, `[1, 2]`, `{"key": value}`, `(a, b)` |
| Variables     | `user`, `user.name`, `user["name"]`, `items[0]`, `items[-1]`, `items[1:3]`, `text[:10]`     |
| Arithmetic    | `+ - * / // % **` (`/` gives a float, `//` and `%` round towards minus infinity)            |
| Text          | `~` joins as text: `"Page " ~ n`; `+` joins strings and lists; `"ab" * 3`                  |
| Comparison    | `== != < <= > >=`, `in`, `not in`                                                           |
| Logic         | `and`, `or`, `not` (`a or "fallback"` returns the first true value, like Python)          |
| Conditional   | `"yes" if flag else "no"`                                                                  |
| Filters       | `name|lower`, `items|join(", ")`, `list|sort(attribute="age", reverse=true)`, `text|head:10` |
| Tests         | `n is even`, `x is not defined`, `n is divisibleby 3`, `x is in(list)`                     |
| Calls         | `macro(1, name="x")`, `range(5)`, `loop.cycle("a", "b")`, `text.upper()` (filters and tests can be called as methods) |

Missing variables and attributes are undefined: they render as nothing and are false in conditions (unless
`strictUndefined` is set).

### Statements

```
{% if cond %} ... {% elif other %} ... {% else %} ... {% endif %}

{% for item in items %} ... {% else %} (no items) {% endfor %}
{% for key, value in map %}   {% for a, b in pairs %}   {% for x in items if x.visible %}
    loop.index, loop.index0, loop.revindex, loop.revindex0, loop.first, loop.last, loop.length,
    loop.previtem, loop.nextitem, loop.depth, loop.cycle(...); {% break %} and {% continue %}

{% set x = expr %}            {% set ns.count = ns.count + 1 %} (on ns = namespace(count=0))
{% set html %}...{% endset %} {% set loud | upper %}...{% endset %}
{% with a = 1, b = 2 %} ... {% endwith %}

{% include "card.html" %}     {% include name_variable %}   {% include ["a.html", "b.html"] %}
{% include "card.html" with item=row title="x" %}   ... only   ... ignore missing

{% extends "base.html" %}     {% block name %} ... {{ super() }} ... {% endblock %}

{% macro button(label, kind="primary") %}<button class="{{ kind }}">{{ label }}</button>{% endmacro %}
{{ button("Save") }}          surplus arguments are in varargs and kwargs
{% call(item) list(items) %}{{ item.name }}{% endcall %}   the macro calls caller(item)
{% import "forms.html" as forms %}{{ forms.button("Go") }}
{% from "forms.html" import button, input as field %}

{% filter upper %} ... {% endfilter %}
{% autoescape false %} ... {% endautoescape %}
{% raw %} {{ shown as is }} {% endraw %}
{% do expr %}                 evaluate and discard
```

Scoping follows Jinja: a `set` inside a loop iteration does not leak out of it (use `namespace()` for counters),
macros see their arguments, the template's top-level variables, the render data and the globals, and an `include`
sees the current scope (with `only`, just its arguments and the globals). In a child template only blocks are
rendered; its top-level `set`, `import` and `from` statements run before the parent is rendered.

### Filters

| Area        | Filters |
|-------------|---------|
| Escaping    | `escape`/`e`, `forceescape`, `safe`/`raw`, `urlencode`/`url`, `tojson`/`json` (safe for `<script>`), `xmlattr` |
| Text        | `lower`, `upper`, `capitalize`, `title`, `trim(chars)`, `replace(old, new, count)`, `truncate(length=255, killwords=false, end="...", leeway=0)`, `head(n)`, `prefix(text)`, `suffix(text)`, `wordcount`, `striptags`, `indent(width=4, first=false, blank=false)`, `center(width)`, `nl2br`, `format(args...)` (`%s`, `%d`, `%f`, `%.2f`), `split(sep)`, `string` |
| Numbers     | `int(default=0)`, `float(default=0.0)`, `abs`, `round(precision=0, method="common"/"ceil"/"floor")`, `thousands(sep=",")`, `filesizeformat(binary=false)` |
| Collections | `length`/`count`, `first`, `last`, `list`, `reverse`, `join(sep, attribute)`, `sort(reverse, case_sensitive, attribute)`, `dictsort(case_sensitive, by="key"/"value", reverse)`, `unique(case_sensitive, attribute)`, `min`/`max(case_sensitive, attribute)`, `sum(attribute, start=0)`, `batch(size, fill_with)`, `slice(columns)`, `groupby(attribute)` (items with `grouper` and `list`), `keys`, `values`, `items`, `attr(name)` |
| Selection   | `map(attribute="x")`, `map("filter", args...)`, `select("test", args...)`, `reject(...)`, `selectattr("attr", "test", args...)`, `rejectattr(...)` |
| Other       | `default(value="", boolean=false)`/`d` (replaces undefined and null; with `boolean=true` every false value) |

Attribute arguments accept dotted paths such as `"author.name"`. Filters with one argument can also be written in the
short form `value|name:arg`.

### Tests

`defined`, `undefined`, `none`/`null`, `boolean`, `true`, `false`, `number`, `integer`, `float`, `string`, `mapping`,
`list`, `iterable`, `sequence`, `callable`, `empty`, `safe`, `even`, `odd`, `divisibleby(n)`, `eq`/`==`, `ne`/`!=`,
`lt`/`<`, `le`/`<=`, `gt`/`>`, `ge`/`>=`, `in(collection)`, `sameas(value)`, `lower`, `upper`, `startingwith(prefix)`,
`endingwith(suffix)`

### Functions

`range(stop)` / `range(start, stop, step)`, `dict(key=value, ...)`, `namespace(key=value, ...)`, `super()` inside a
block, `caller(args)` inside a macro that was called with `{% call %}`, plus your own from `addFunction`.

## Escaping

With `autoescape` on (the default), `{{ }}` escapes `& < > " '` unless the value is safe. Values become safe through
`|safe`, `|escape`, `templateSafe(...)`, or by being markup the engine produced: macro output, `caller()`, `super()`,
`{% set %}` blocks and filters like `tojson`, `xmlattr` and `nl2br`. Joining safe markup with `~` escapes the unsafe side
first, so `"<b>"|safe ~ user_input` stays correct.

## Errors

Mistakes never crash: `add` returns `false` for syntax errors, and `render` returns an error `Result` for compile and
runtime errors (unknown filters or templates, wrong types, division by zero, endless recursion). `lastError` names the
template and line:

```
page.html:12: 'if' block is never closed
page.html:3: unknown filter 'titel'
partials/row.html:1: cannot compare int and string
```

Run `engine.check()` at startup or in a test to catch broken templates and missing includes early.
