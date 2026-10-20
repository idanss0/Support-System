# Support-System
Support overview dashboards and reports

- [MVP spec: Support Control Tower (Hebrew)](docs/MVP-Support-Control-Tower.md), also as [Word](docs/MVP-Support-Control-Tower.docx) and [PDF](docs/MVP-Support-Control-Tower.pdf)
- [Short MVP (Hebrew)](docs/MVP-Short.md), also as [Word](docs/MVP-Short.docx) and [PDF](docs/MVP-Short.pdf)
- [Mobile MVP on Spotfire (Hebrew)](docs/MVP-Mobile.md), also as [Word](docs/MVP-Mobile.docx) and [PDF](docs/MVP-Mobile.pdf); [phone mockup](docs/dashboards/mobile.html)
- [Dashboard mockup (synthetic data)](docs/dashboards/index.html), screenshots in `docs/dashboards/img/`

Rebuild the Word file after editing the Markdown:

```
cd tools && npm install && node md-to-docx.js ../docs/MVP-Support-Control-Tower.md ../docs/MVP-Support-Control-Tower.docx
```

## Obsidian notes

`tools/obsidian_sync.py` builds Obsidian notes from `docs/` and the hand-written notes in `obsidian/`, and copies them to `<vault>/מערכת מעקב תמיכה טכנית/`. It needs Python 3.8+ and nothing else.

```
python -I tools/obsidian_sync.py "C:/Obsidian_Vault"
```

To run it automatically after every Claude Code response, copy `.claude/settings.local.json.example` to `.claude/settings.local.json` (not committed) and adjust the vault path. The script writes only inside that project folder, never deletes, backs up a note edited in Obsidian (to `.sync-backup/`) before overwriting it, and always exits 0. Edit the notes in the repo, not in the vault: the repo is the source.
