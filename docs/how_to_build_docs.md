# Building and extending the documentation

This project uses **[MkDocs](https://www.mkdocs.org/)** with the **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)** theme. All site pages live under the `docs/` directory as **Markdown** (`.md`) files.

---

## Prerequisites

From the repository root, use the **dev** dependency group (includes `mkdocs`, `mkdocs-material`, `mkdocstrings`):

```bash
cd /path/to/dialograph
uv sync --group dev
```

---

## Run a local doc server (preview)

```bash
uv run mkdocs serve
```

Open the URL MkDocs prints (usually **http://127.0.0.1:8000**). Edits to files under `docs/` reload automatically.

---

## Build static HTML (for hosting)

```bash
uv run mkdocs build
```

Output is written to the **`site/`** directory at the repo root. Point any static host (GitHub Pages, Netlify, etc.) at that folder after upload, or use `mkdocs gh-deploy` if you use the `gh-pages` workflow.

---

## Add a new Markdown page

1. **Create** a file under `docs/`, for example `docs/my_page.md`.

2. **Register** it in **`mkdocs.yml`** under `nav:` so it appears in the sidebar. Example:

   ```yaml
   nav:
     - Home: index.md
     - My section:
         - My page: my_page.md
   ```

3. **Link** from other pages with normal Markdown:

   ```markdown
   See [My page](my_page.md).
   ```

Paths in `nav` and in links are **relative to the `docs/` folder** (MkDocs default `docs_dir`).

4. Re-run **`mkdocs serve`** or refresh the browser to see changes.

---

## Configuration file

- **`mkdocs.yml`** (repository root) sets `site_name`, theme, plugins, and `nav`.
- API pages under `docs/api/` use **mkdocstrings** (`::: package.module.Class`) to pull docstrings from Python code in `src/`.

---

## Math (LaTeX) in Markdown

Pages such as [Formal mechanics (`real_run3`)](real_run3_formal_mechanics.md) contain `\(...\)` and `\[...\]` math. To render them in the browser you must enable a math extension (e.g. **Arithmatex** + MathJax) in `mkdocs.yml`; see [Material: Math](https://squidfunk.github.io/mkdocs-material/reference/math/). Until that is configured, math may appear as raw LaTeX in the HTML preview.

---

## Troubleshooting

| Issue | What to try |
|--------|-------------|
| `mkdocs: command not found` | Run via `uv run mkdocs ...` after `uv sync --group dev`. |
| mkdocstrings cannot import `dialograph` | The handler is configured with `paths: [src]` in `mkdocs.yml` so packages resolve from `src/`. |
| Page exists but warning “not included in nav” | Add the file under `nav:` in `mkdocs.yml`, or ignore the warning if you intentionally use only deep links. |
