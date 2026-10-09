"""Build album image assets and a JSON index from content/album/*/index.md.

Albums live only on the intranet host, not in the Git repository. Each
folder has an index.md and photos. Generating resized images never changes
the originals under content/album/.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import markdown
import yaml
from PIL import Image, ImageOps

IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}
FRONTMATTER = re.compile(r'\A---\s*\n(.*?)\n---\s*(?:\n|\Z)', re.S)
DATE_FORMAT = re.compile(r'\A(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?\Z')
MAX_PHOTO_EDGE = 1800


def load_album_metadata(path: Path):
    text = path.read_text(encoding='utf-8-sig')
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError(f'Expected YAML frontmatter in {path}; see maintainers/album-guide.md')
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError(f'Invalid metadata in {path}')
    title = str(data.get('title', '')).strip()
    raw_date = data.get('date', '')
    date_text = raw_date.isoformat() if isinstance(raw_date, date) else str(raw_date).strip()
    if not title or not DATE_FORMAT.fullmatch(date_text):
        raise ValueError(f'{path}: title and date (YYYY, YYYY-MM, or YYYY-MM-DD) are required')
    match_date = DATE_FORMAT.fullmatch(date_text)
    year, month, day = (int(s or 0) for s in match_date.groups())
    if not (0 <= month <= 12 and 0 <= day <= 31) or (day and not month):
        raise ValueError(f'Invalid date: {date_text} in {path}')
    if month and day:
        date(year, month, day)  # reject impossible calendar dates
    return data, title, date_text, match.end(), text


def build_albums(project_root: Path, preview_root: Path):
    source = project_root / 'content' / 'album'
    assets = preview_root / 'assets' / 'album-photos'
    assets.mkdir(parents=True, exist_ok=True)

    albums = []
    for folder in sorted(source.iterdir()) if source.is_dir() else []:
        if not folder.is_dir() or folder.name.startswith('.'):
            continue
        if not re.fullmatch(r'[A-Za-z0-9_-]+', folder.name):
            raise ValueError(f'Album folder must have URL-friendly name: {folder.name}')
        meta_path = folder / 'index.md'
        if not meta_path.is_file():
            # Do not accidentally publish an unfinished photo folder.
            continue
        data, title, event_date, begin, original = load_album_metadata(meta_path)
        pictures = sorted((p for p in folder.iterdir()
                          if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES),
                         key=lambda p: p.name.casefold())
        if not pictures:
            # A partially uploaded album isn't ready for publication yet.
            continue

        # Optional cover prioritizes a selected thumbnail. Without it, the
        # lexicographically first photo automatically becomes the cover.
        cover = str(data.get('cover', '')).strip()
        if cover:
            photo = folder / cover
            if photo not in pictures:
                raise ValueError(f'{meta_path}: cover {cover!r} is not one of this album\'s photos')
            pictures.remove(photo)
            pictures.insert(0, photo)

        images = []
        for i, picture in enumerate(pictures, 1):
            destination = assets / f'{folder.name}-{i:02}.jpg'
            if not destination.is_file() or destination.stat().st_mtime_ns < picture.stat().st_mtime_ns:
                with Image.open(picture) as im:
                    # Phone camera EXIF can say rotate by 90/270 degrees.
                    # Apply it to the pixels before removing EXIF in the copy.
                    corrected = ImageOps.exif_transpose(im)
                    corrected.thumbnail((MAX_PHOTO_EDGE, MAX_PHOTO_EDGE), Image.Resampling.LANCZOS)
                    if corrected.mode != 'RGB':
                        corrected = corrected.convert('RGB')
                    corrected.save(destination, format='JPEG', quality=84, optimize=True)
            images.append('./assets/album-photos/' + destination.name)
        description = original[begin:].strip()
        entry = {
            'id': folder.name,
            'title': title,
            'date': event_date,
            'images': images,
        }
        if description:
            entry['description_html'] = markdown.markdown(description,
                                                         extensions=['fenced_code', 'tables'])
        if data.get('source_url'):
            entry['source_url'] = str(data['source_url'])
        albums.append(entry)


    # An unspecified day/month is sorted before a known day/month in the same
    # year, without inventing a calendar date for the event.
    albums.sort(key=lambda a: tuple(int(x) for x in (a['date'].split('-') + ['0', '0'])[:3]),
                reverse=True)
    # Only this directory contains generated album photos. Prune stale
    # converted copies if a photo was deleted or an album was retired.
    active_images = {Path(photo).name for album in albums for photo in album['images']}
    for old_image in assets.iterdir():
        if old_image.is_file() and old_image.suffix.lower() in IMAGE_SUFFIXES:
            if old_image.name not in active_images:
                old_image.unlink()
    (preview_root / 'albums.json').write_text(
        json.dumps(albums, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return albums
