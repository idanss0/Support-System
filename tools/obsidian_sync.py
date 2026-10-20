#!/usr/bin/env python3
"""Copy the project notes into an Obsidian vault.

Builds an Obsidian note from each document in docs/, copies the PDFs and the
images they embed, and copies the hand-written notes in obsidian/. Everything
goes to <vault>/<PROJECT_FOLDER>/.

Meant to run as a Claude Code Stop hook (see .claude/settings.local.json.example):

    python -I tools/obsidian_sync.py "C:/Obsidian_Vault" --hook

Safety rules:
- Writes only inside <vault>/<PROJECT_FOLDER>. Never deletes anything.
- Before overwriting a file it did not write itself (for example a note edited
  in Obsidian), it saves a copy under <PROJECT_FOLDER>/.sync-backup/.
- Always exits 0, so it never blocks Claude Code. Problems are reported as text
  (or, with --hook, as a systemMessage).
- Standard library only.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

PROJECT_FOLDER = 'מערכת מעקב תמיכה טכנית'
GH = 'https://github.com/idanss0/Support-System/tree/claude/support-tracking-system-mvp-e26kbf'
DOCS = [
    # (source md in docs/, note title, status, pdf in docs/)
    ('MVP-Short.md', 'MVP מקוצר - מסך חי', 'התוכנית הנוכחית', 'MVP-Short.pdf'),
    ('MVP-Support-Control-Tower.md', 'MVP מלא', 'תוכנית לגלים הבאים', 'MVP-Support-Control-Tower.pdf'),
    ('MVP-Mobile.md', 'MVP אפליקציה לטלפון', 'על גבי Spotfire, חלק מה-MVP', 'MVP-Mobile.pdf'),
]
# cross-references between documents become wikilinks
XREFS = [
    ('מסמך MVP-Mobile', 'מסמך [[MVP אפליקציה לטלפון]]'),
    ('(MVP-Mobile)', '([[MVP אפליקציה לטלפון]])'),
    ('MVP-Support-Control-Tower (', '[[MVP מלא]] ('),
    ('(MVP-Short)', '([[MVP מקוצר - מסך חי]])'),
]
IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
STATE_FILE = '.sync-state.json'
BACKUP_DIR = '.sync-backup'
ATTACHMENTS = 'attachments'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inside(base, path):
    """True if path (resolved) is base or below it."""
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def find_image(repo, name):
    """Find an image by bare file name under docs/. Returns a Path or None."""
    if Path(name).name != name or Path(name).suffix.lower() not in IMAGE_EXT:
        return None
    for p in sorted((repo / 'docs').rglob(name)):
        if p.is_file() and inside(repo / 'docs', p):
            return p
    return None


def convert_doc(repo, src, status, pdf, outputs, warnings):
    """Return the Obsidian note for one document, adding its images to outputs."""
    docs = repo / 'docs'
    text = (docs / src).read_text(encoding='utf-8')
    text = '\n'.join(l for l in text.split('\n') if l.strip() not in ('<div dir="rtl">', '</div>'))

    def image(m):
        alt, ref = m.group(1), m.group(2).strip()
        if '://' in ref:
            return m.group(0)  # external image, leave as is
        path = (docs / ref)
        if not inside(docs, path) or path.suffix.lower() not in IMAGE_EXT or not path.is_file():
            warnings.append('%s: תמונה לא נמצאה או לא מותרת: %s' % (src, ref))
            return m.group(0)
        width = ''
        if '|' in alt:
            alt, pct = alt.rsplit('|', 1)
            if pct.strip().isdigit():
                width = '|%d' % int(int(pct) * 7.5)
        outputs[ATTACHMENTS + '/' + path.name] = path.read_bytes()
        return '![[%s%s]]' % (path.name, width)

    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', image, text)
    for old, new in XREFS:
        text = text.replace(old, new)

    date = re.search(r'\|\s*\*\*תאריך\*\*\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|', text)
    fm = '---\ntags:\n  - support-system\n  - mvp\nstatus: %s\n' % status
    if date:
        fm += 'updated: %s\n' % date.group(1)
    fm += 'source: %s\npdf: "[[%s]]"\n---\n\n' % (GH, pdf)
    nav = '> חלק מ-[[%s]]. גרסת PDF: [[%s]]\n\n' % (PROJECT_FOLDER, pdf)
    return fm + nav + text.lstrip('\n')


def build(repo):
    """Build every output in memory: {relative path in the project folder: bytes}."""
    outputs, warnings = {}, []
    for src, title, status, pdf in DOCS:
        if not (repo / 'docs' / src).is_file():
            warnings.append('חסר מסמך: docs/%s' % src)
            continue
        note = convert_doc(repo, src, status, pdf, outputs, warnings)
        outputs[title + '.md'] = note.encode('utf-8')
        if (repo / 'docs' / pdf).is_file():
            outputs[ATTACHMENTS + '/' + pdf] = (repo / 'docs' / pdf).read_bytes()
        else:
            warnings.append('חסר PDF: docs/%s' % pdf)

    # hand-written notes, copied as they are, plus the images they embed
    for note in sorted((repo / 'obsidian').glob('*.md')):
        data = note.read_bytes()
        outputs[note.name] = data
        for name in re.findall(r'!\[\[([^\]|#]+)', data.decode('utf-8', 'replace')):
            name = name.strip()
            if Path(name).suffix.lower() not in IMAGE_EXT:
                continue
            img = find_image(repo, name)
            if img:
                outputs[ATTACHMENTS + '/' + name] = img.read_bytes()
            else:
                warnings.append('%s: תמונה לא נמצאה: %s' % (note.name, name))
    return outputs, warnings


def write_atomic(dest, data):
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(dest.parent), prefix='.sync-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        os.chmod(tmp, 0o644)  # mkstemp creates 0600; keep notes readable like any other file
        os.replace(tmp, str(dest))
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)  # our own temp file only
        raise


def load_state(target):
    try:
        state = json.loads((target / STATE_FILE).read_text(encoding='utf-8'))
        if isinstance(state, dict) and isinstance(state.get('files'), dict):
            return state
    except (OSError, ValueError):
        pass
    return {'source': None, 'files': {}}


def sync(repo, vault, force=False):
    """Returns (list of messages, list of warnings)."""
    if not vault.is_dir():
        return [], ['לא נמצא כספת Obsidian בנתיב: %s. לא סונכרן דבר.' % vault]
    target = vault / PROJECT_FOLDER
    if target.is_symlink() or (target.exists() and not inside(vault, target)):
        return [], ['תיקיית הפרויקט בכספת היא קישור לנתיב אחר. לא סונכרן דבר: %s' % target]

    outputs, warnings = build(repo)
    source = sha(json.dumps(sorted((k, sha(v)) for k, v in outputs.items())).encode())
    state = load_state(target)
    if (not force and state.get('source') == source
            and all((target / rel).is_file() for rel in outputs)):
        return [], warnings  # nothing changed since the last sync

    written, backed_up = [], []
    stamp = time.strftime('%Y%m%d-%H%M%S')
    for rel, data in sorted(outputs.items()):
        dest = target / rel
        if dest.is_symlink() or not inside(target, dest.parent if dest.parent.exists() else target):
            warnings.append('דילגתי על %s: קישור או נתיב מחוץ לתיקיית הפרויקט' % rel)
            continue
        try:
            if dest.is_file():
                current = sha(dest.read_bytes())
                if current == sha(data):
                    state['files'][rel] = current
                    continue
                if current != state['files'].get(rel):
                    # not what we wrote last time: keep a copy before overwriting
                    write_atomic(target / BACKUP_DIR / stamp / rel, dest.read_bytes())
                    backed_up.append(rel)
            write_atomic(dest, data)
            state['files'][rel] = sha(data)
            written.append(rel)
        except OSError as e:
            warnings.append('לא הצלחתי לכתוב את %s: %s' % (rel, e))

    state['source'] = source
    try:
        write_atomic(target / STATE_FILE, json.dumps(state, ensure_ascii=False, indent=1).encode('utf-8'))
    except OSError as e:
        warnings.append('לא הצלחתי לשמור את קובץ המצב: %s' % e)

    messages = []
    if written:
        count = 'קובץ אחד' if len(written) == 1 else '%d קבצים' % len(written)
        messages.append('Obsidian: עודכנו %s ב-%s' % (count, target))
    if backed_up:
        messages.append('נשמר עותק של %d קבצים שנערכו בכספת, ב-%s' % (
            len(backed_up), target / BACKUP_DIR / stamp))
    return messages, warnings


def main(argv):
    hook = '--hook' in argv
    force = '--force' in argv
    rest = [a for a in argv if a not in ('--hook', '--force')]
    try:
        if len(rest) != 1 or rest[0].startswith('-'):
            messages, warnings = [], ['שימוש: obsidian_sync.py <נתיב לכספת> [--force] [--hook]']
        else:
            repo = Path(__file__).resolve().parent.parent
            messages, warnings = sync(repo, Path(rest[0]).expanduser(), force)
    except Exception as e:  # never break Claude Code over a sync problem
        messages, warnings = [], ['הסנכרון ל-Obsidian נכשל: %s: %s' % (type(e).__name__, e)]

    lines = messages + ['אזהרה: ' + w for w in warnings]
    if hook:
        if lines:
            print(json.dumps({'systemMessage': '\n'.join(lines)}))  # ASCII-escaped JSON
    else:
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError):
            pass
        print('\n'.join(lines) if lines else 'Obsidian: אין שינויים.')
    return 0


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    finally:
        sys.exit(0)
