#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTS = {'.md', '.txt', '.rst', '.yml', '.yaml', '.json', '.py', '.sh', '.toml', '.ini'}
SKIP_PATHS = {
    'scripts/check_runtime_baseline.py',
}
ALLOW_CONTEXT = [
    'inactive',
    'not supported in current baseline',
    'future extension candidate',
    'historical',
    'roadmap',
    'do not introduce',
    'excluded from active execution',
]
BANNED_RUNTIME_PHRASES = [
    'selectable runtime',
    'runtime selection',
    'select runtime',
    'multi-backend',
    'multiple backends',
    'claw backend',
]
ACTIVE_PATH_HINTS = [
    'install.sh',
    'little7-installer/',
    'scripts/',
    'supervisor/',
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


def allowed(line: str) -> bool:
    lowered = line.lower()
    return any(token in lowered for token in ALLOW_CONTEXT)


def in_active_path(rel: str) -> bool:
    return any(hint in rel for hint in ACTIVE_PATH_HINTS)


def main() -> int:
    violations: list[str] = []
    for path, rel in iter_files():
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except Exception:
            continue

        for lineno, line in enumerate(lines, start=1):
            lowered = line.lower()
            if allowed(line):
                continue

            if 'nanoclaw' in lowered or 'nano claw' in lowered or 'nano-claw' in lowered:
                if in_active_path(rel):
                    violations.append(f'{rel}:{lineno}: NanoClaw appears in active/runtime path -> {line.strip()}')
                continue

            if any(phrase in lowered for phrase in BANNED_RUNTIME_PHRASES):
                if in_active_path(rel) or 'runtime' in lowered or 'backend' in lowered:
                    violations.append(f'{rel}:{lineno}: runtime drift phrase -> {line.strip()}')
                continue

    if violations:
        print('Runtime baseline violations found:')
        for item in violations:
            print(item)
        return 1

    print('[PASS] Runtime baseline intact: OpenClaw only, no NanoClaw execution path.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
