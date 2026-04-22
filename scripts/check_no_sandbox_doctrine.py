#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTS = {'.md', '.txt', '.rst', '.yml', '.yaml', '.json', '.py', '.sh', '.toml', '.ini'}
SKIP_PATHS = {
    'docs/ALPHA_BASELINE_MANIFEST.md',
    'scripts/check_no_sandbox_doctrine.py',
}
ANTI_PATTERNS = [
    'describe sandbox as a security boundary',
    'describes sandbox as protection',
    'uses vm or container isolation as security justification',
    'must not',
    'does not rely',
    'do not',
    'not adopted',
    'outside the system',
    'historical',
    'deprecated',
]
BANNED_PHRASES = [
    'sandbox protects',
    'sandbox provides safety',
    'sandbox provides security',
    'sandbox is a security boundary',
    'sandboxing for security',
    'container isolation',
    'secure environment',
    'isolated execution',
    'containment = protection',
]


def iter_files():
    for path in ROOT.rglob('*'):
        if not path.is_file():
            continue
        if '.git' in path.parts or '__pycache__' in path.parts:
            continue
        if path.suffix.lower() not in TEXT_EXTS:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in SKIP_PATHS:
            continue
        yield path, rel


def main() -> int:
    violations = []
    for path, rel in iter_files():
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except Exception:
            continue

        for lineno, line in enumerate(lines, start=1):
            lowered = line.lower()

            if any(p in lowered for p in ANTI_PATTERNS):
                continue

            if any(phrase in lowered for phrase in BANNED_PHRASES):
                violations.append(f'{rel}:{lineno}: banned phrase -> {line.strip()}')
                continue

            if 'sandbox' in lowered and any(tok in lowered for tok in ['protect', 'protection', 'security boundary', 'safe by', 'safety by']):
                violations.append(f'{rel}:{lineno}: sandbox used as security justification -> {line.strip()}')
                continue

            if 'container' in lowered and any(tok in lowered for tok in ['protect', 'protection', 'security boundary', 'safe by', 'safety by']):
                violations.append(f'{rel}:{lineno}: container used as security justification -> {line.strip()}')
                continue

    if violations:
        print('Sandbox doctrine violations found:')
        for item in violations:
            print(item)
        return 1

    print('[PASS] No sandbox-doctrine violations found.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
