"""Compile server-local handbooks from content/handbooks/<id>/ folders."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import yaml
from textbook_builder import FRONTMATTER, save_cover


def build_handbooks(project_root: Path, output_root: Path):
    source = project_root / 'content' / 'handbooks'
    pdf_dir = output_root / 'files' / 'handbooks'
    cover_dir = output_root / 'assets' / 'handbook-covers'
    pdf_dir.mkdir(parents=True, exist_ok=True)
    cover_dir.mkdir(parents=True, exist_ok=True)
    items = []
    for folder in sorted(source.iterdir()) if source.is_dir() else []:
        if not folder.is_dir() or folder.name.startswith('.'):
            continue
        if not re.fullmatch(r'[A-Za-z0-9_-]+', folder.name):
            raise ValueError(f'Invalid handbook folder name: {folder.name}')
        md, pdf = folder / 'index.md', folder / 'book.pdf'
        if not md.is_file() or not pdf.is_file():
            continue
        match = FRONTMATTER.match(md.read_text(encoding='utf-8-sig'))
        if not match:
            raise ValueError(f'Expected YAML frontmatter in {md}')
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict) or not all(data.get(k) for k in ('title','year','kind')):
            raise ValueError(f'{md}: title, year and kind are required')
        if data['kind'] not in ('保研', '飞跃'):
            raise ValueError(f'{md}: kind must be 保研 or 飞跃')
        shutil.copy2(pdf, pdf_dir / (folder.name + '.pdf'))
        save_cover(folder, pdf, cover_dir / (folder.name + '.jpg'))
        items.append({
            'id': folder.name,
            'title': str(data['title']),
            'year': str(data['year']),
            'kind': str(data['kind']),
            'pdf': f'./files/handbooks/{folder.name}.pdf',
            'cover': f'./assets/handbook-covers/{folder.name}.jpg',
        })
    (output_root / 'handbooks.json').write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return items
