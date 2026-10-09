"""Compile server-local textbooks from content/textbooks/<id>/index.md + book.pdf.

None of these book folders or files are kept in Git. An empty collection
is valid and produces an empty JSON index on a newly cloned checkout.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import yaml
from PIL import Image, ImageOps

FRONTMATTER = re.compile(r'\A---\s*\n(.*?)\n---\s*(?:\n|\Z)', re.S)
COVER_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')


def override_for(book_folder: Path):
    images = [book_folder / ('cover' + ext) for ext in COVER_EXTENSIONS
              if (book_folder / ('cover' + ext)).is_file()]
    if len(images) > 1:
        raise ValueError(f'One cover.* image per book is allowed: {book_folder}')
    return images[0] if images else None


def generate_cover(pdf: Path, output: Path):
    """Generate a JPEG thumbnail from page one; called only without cover.*."""
    pdftoppm = shutil.which('pdftoppm')
    if not pdftoppm:
        raise RuntimeError('Install Poppler pdftoppm to generate covers from PDF files')
    temporary = output.with_name(output.stem + '.rendering.jpg')
    try:
        subprocess.run([
            pdftoppm, '-f', '1', '-l', '1', '-singlefile',
            '-scale-to', '1000', '-jpeg', '-jpegopt', 'quality=86,optimize=y',
            str(pdf), str(temporary.with_suffix('')),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=90)
        if not temporary.is_file():
            raise RuntimeError(f'PDF has no renderable first page: {pdf}')
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def save_cover(folder: Path, book: Path, destination: Path):
    image = override_for(folder)
    if image is None:
        generate_cover(book, destination)
    else:
        with Image.open(image) as original:
            result = ImageOps.exif_transpose(original)
            result.thumbnail((1000, 1250), Image.Resampling.LANCZOS)
            if result.mode != 'RGB':
                result = result.convert('RGB')
            result.save(destination, format='JPEG', quality=87, optimize=True)


def build_textbooks(project_root: Path, output_root: Path):
    source = project_root / 'content' / 'textbooks'
    pdf_dir = output_root / 'files' / 'textbooks'
    cover_dir = output_root / 'assets' / 'textbook-covers'
    pdf_dir.mkdir(parents=True, exist_ok=True)
    cover_dir.mkdir(parents=True, exist_ok=True)
    items = []
    for folder in sorted(source.iterdir()) if source.is_dir() else []:
        if not folder.is_dir() or folder.name.startswith('.'):
            continue
        if not re.fullmatch(r'[A-Za-z0-9_-]+', folder.name):
            raise ValueError(f'Invalid textbook folder name: {folder.name}')
        md, pdf = folder / 'index.md', folder / 'book.pdf'
        # Empty folders are normal on GitHub. Incomplete uploads are not listed.
        if not md.is_file() or not pdf.is_file():
            continue
        match = FRONTMATTER.match(md.read_text(encoding='utf-8-sig'))
        if not match:
            raise ValueError(f'Expected YAML frontmatter in {md}')
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict) or not all(data.get(k) for k in ('title','subject')):
            raise ValueError(f'{md}: title and subject are required')
        destination = pdf_dir / (folder.name + '.pdf')
        shutil.copy2(pdf, destination)
        cover = cover_dir / (folder.name + '.jpg')
        save_cover(folder, pdf, cover)
        items.append({
            'subject': str(data['subject']),
            'title': str(data['title']),
            'pdf': f'./files/textbooks/{folder.name}.pdf',
            'cover': f'./assets/textbook-covers/{folder.name}.jpg',
        })
    (output_root / 'textbooks.json').write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return items
