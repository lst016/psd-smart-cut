# Cursor Integration Guide

This guide is for opening PSD Smart Cut in Cursor and getting imports, commands, and navigation working cleanly.

## Open the Repository Root

Open the actual project root in Cursor:

```text
psd-smart-cut/
```

Do not hard-code a machine-specific absolute path into shared project docs or settings.

## Python Import Behavior

The stable package namespace is:

```python
skills.psd_parser
```

If Cursor needs extra import help, point it at the repository root so `skills` resolves correctly.

## Recommended Checks

Run these from the integrated terminal:

```bash
pip install -r requirements.txt
python -m skills.cli --help
python -m pytest skills/psd-parser -q
```

## Useful Files

```text
README.md
docs/guides/usage.md
docs/guides/USER_GUIDE.md
examples/basic_parse.py
skills/cli.py
skills/psd_parser/__init__.py
skills/psd-parser/level9-integration/pipeline.py
```

## Common Workflow

1. inspect Level 1 parsing behavior with `examples/basic_parse.py`
2. validate CLI behavior with `python -m skills.cli --help`
3. run `run_full_pipeline(...)` or the CLI `process` command for end-to-end flows
4. use `python -m pytest skills/psd-parser -q` before finalizing changes

## Notes

- The implementation folders still use some legacy filesystem names such as `psd-parser` and `level1-parse`.
- Public-facing Python imports should still go through `skills.psd_parser`.
- The repository currently ships one maintained example script rather than a larger examples catalog.
