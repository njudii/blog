#!/usr/bin/env python3
"""Build the internal DII static website from articles and local resources.

The repository contains shareable source only. Handbooks and textbooks are
provided privately by the intranet host inside their content/ directories.
The generated dist/ output is always ignored by Git.
"""
from __future__ import annotations

import html
import hashlib
import json
import re
import shutil
import tomllib
import yaml
from pathlib import Path
from itertools import groupby
from urllib.parse import unquote, urlparse
import markdown
from album_builder import build_albums
from announcement import render_home_announcement
from textbook_builder import build_textbooks
from handbook_builder import build_handbooks
from markdown_extensions import StrikethroughExtension

SOURCE_DIR = Path(__file__).resolve().parent
PROJECT = SOURCE_DIR.parent
HERE = PROJECT / 'dist'  # generated output, never tracked in Git
ARTICLES_DIR = PROJECT / 'content' / 'articles'
DEST_ARTICLES = HERE / 'articles'
DEST_FIG = HERE / 'fig'
DEST_FILES = HERE / 'files'


def esc(value):
    return html.escape(str(value or ""), quote=True)


def load_sections():
    """Discover all article sections from their YAML metadata.

    Adding content/articles/new-section/_section.md and a published article
    is sufficient to add navigation, index page, post pages and feed data.
    """
    sections = []
    files_used = {'index.html', 'photos.html'}
    for directory in sorted(ARTICLES_DIR.iterdir()):
        if not directory.is_dir() or directory.name.startswith(('.', '_')):
            continue
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', directory.name):
            raise ValueError(f'Section slug must be URL-friendly: {directory.name}')
        config = directory / '_section.md'
        if not config.is_file():
            raise ValueError(f'Missing section configuration: {config}')
        raw = config.read_text(encoding='utf-8-sig')
        match = re.match(r'\A---\s*\n(.*?)\n---\s*(?:\n|\Z)',raw,re.S)
        if not match:
            raise ValueError(f'Section needs YAML frontmatter: {config}')
        data = yaml.safe_load(match.group(1))
        if not isinstance(data,dict) or not str(data.get('title','')).strip():
            raise ValueError(f'Section title missing: {config}')
        page = str(data.get('page', directory.name + '.html'))
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]*\.html', page) or page in files_used:
            raise ValueError(f'Invalid/duplicate section page {page}: {config}')
        feature = data.get('feature','')
        if feature not in ('','handbooks','textbooks'):
            raise ValueError(f'Unknown special feature {feature} at {config}')
        order = int(data.get('order',100))
        sections.append({
          'id':directory.name,'title':str(data['title']),'page':page,
          'order':order,'feature':feature,
          'list_title':str(data.get('list_title','文章')),
          'description':str(data.get('description','')),
          'list_style':str(data.get('list_style','archive')),
          'show_empty':bool(data.get('show_empty',False)),
        })
        files_used.add(page)
    return sorted(sections,key=lambda s:(s['order'],s['id']))


SECTIONS = []
ARTICLES = []


def section_for(section_id):
    return next(section for section in SECTIONS if section['id']==section_id)


def layout(title, body, current='', depth=0, top_banner=''):
    root = '../' if depth else './'
    script_version = hashlib.sha256((SOURCE_DIR / 'app.js').read_bytes()).hexdigest()[:10]
    nav = [('首页','index.html','home')]
    for section in SECTIONS:
        if section['show_empty'] or section['feature'] or any(p['section']==section['id'] for p in ARTICLES):
            nav.append((section['title'],section['page'],section['id']))
    nav.append(('活动相册','photos.html','photos'))
    links = ''.join(
        f'<a href="{root}{esc(page)}"' +
        (' aria-current="page"' if current==key else '') +
        f'>{esc(label)}</a>' for label,page,key in nav
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#f8fafc">
  <meta name="description" content="DII 的博客：南京大学匡亚明学院学生分享平台。">
  <title>{esc(title)} · DII 的博客</title>
  <link rel="stylesheet" href="{root}styles.css">
  <script src="{root}app.js?v={script_version}" defer></script>
</head>
<body>
<a class="skip-link" href="#main">跳到正文</a>
<header class="site-header">
  <div class="header-inner">
    <a class="site-brand" href="{root}index.html" aria-label="南京大学匡亚明学院，返回首页">
      <span class="symbol-orbit" aria-hidden="true"><i></i><i></i><i></i><b></b></span>
      <img class="brand-wordmark" src="{root}assets/college-wordmark.png" alt="南京大学匡亚明学院">
    </a>
    <nav class="main-nav" aria-label="主导航">{links}</nav>
  </div>
</header>
{top_banner}<main id="main">{body}</main>
</body>
</html>
"""


def article_data():
    posts = []
    slugs = set()
    for section in SECTIONS:
        for file in sorted((ARTICLES_DIR / section['id']).glob('*/index.md')):
            slug = file.parent.name
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug):
                raise ValueError(f'Article folder must use lowercase kebab-case: {file}')
            if slug in slugs:
                raise ValueError(f'Duplicate article slug across sections: {slug}. Use a unique folder name.')
            slugs.add(slug)
            text = file.read_text(encoding='utf-8')
            match = re.match(r'\s*\+\+\+\s*\n(.*?)\n\+\+\+\s*\n',text,re.S)
            if match:
                try:front = tomllib.loads(match.group(1))
                except tomllib.TOMLDecodeError as error:
                    raise ValueError(f'Invalid TOML frontmatter {file}: {error}') from error
            else:
                match = re.match(r'\A---\s*\n(.*?)\n---\s*(?:\n|\Z)',text,re.S)
                if not match:raise ValueError(f'Article requires YAML/TOML frontmatter: {file}')
                front = yaml.safe_load(match.group(1))
            if not isinstance(front,dict):raise ValueError(f'Invalid metadata: {file}')
            if front.get('draft',False):continue
            title = str(front.get('title',slug)).strip()
            date = str(front.get('date',''))[:10]
            if not title or not date:raise ValueError(f'Article requires title and date: {file}')
            categories = front.get('categories',front.get('category',[]))
            if isinstance(categories,str):categories=[categories]
            authors = front.get('postauthor',front.get('author',[]))
            if isinstance(authors,str):authors=[authors]
            posts.append({
              'slug':slug,'title':title,'date':date,'year':date[:4],
              'section':section['id'],
              'category':str(categories[0]) if categories else '其他',
              'author':'、'.join(map(str,authors)),
              'tags':list(front.get('tags',[])),
              'markdown':text[match.end():],
              'directory':file.parent,
              'url':f'./articles/{slug}.html',
            })
    return sorted(posts,key=lambda p:(p['date'],p['slug']),reverse=True)


def retired_articles():
    """Map posts already in full-text handbooks to their retained PDF copy."""
    return json.loads((SOURCE_DIR / 'retired-articles.json').read_text(encoding='utf-8'))


def create_retired_article_redirects(retired, original_posts):
    """Keep links to former full-text posts working without duplicating the PDF."""
    original_by_slug = {post["slug"]: post for post in original_posts}
    DEST_ARTICLES.mkdir(exist_ok=True)
    for slug, pdf in retired.items():
        if not re.fullmatch(r"[A-Za-z0-9_-]+", slug) or slug not in original_by_slug:
            raise ValueError(f"Unknown archived article: {slug}")
        target = (DEST_ARTICLES / pdf).resolve()
        has_handbook = target.is_relative_to(HERE) and target.is_file()
        title = original_by_slug[slug]["title"]
        if has_handbook:
            brief_page = (f'<div class="wrap inner-page"><p>本文已收录在相关手册中。</p>'
                          f'<p><a href="{esc(pdf)}">在手册中阅读：{esc(title)} ↗</a></p></div>')
            result = layout(title, brief_page, depth=1)
            result = result.replace('</head>',
                f'<meta name="robots" content="noindex">'
                f'<meta http-equiv="refresh" content="0;url={esc(pdf)}">'
                '</head>',1)
        else:
            brief_page = (f'<div class="wrap inner-page"><h1>{esc(title)}</h1>'
                          '<p>本文已收录在相关手册中。当前服务器尚未配置该手册。</p>'
                          '<p>可在「升学经验」中继续浏览其他文章。</p>'
                          '<p><a href="../guides.html">← 返回升学经验</a></p></div>')
            result = layout(title, brief_page, depth=1)
            result = result.replace('</head>', '<meta name="robots" content="noindex"></head>',1)
        (DEST_ARTICLES / f"{slug}.html").write_text(result, encoding="utf-8")


def import_article_figures(posts):
    """Publish a post's companion images from its own content bundle."""
    if DEST_FIG.exists():shutil.rmtree(DEST_FIG)
    DEST_FIG.mkdir(parents=True,exist_ok=True)
    for post in posts:
        folder = post['directory']
        for src in folder.rglob('*'):
            if not src.is_file() or src.name == 'index.md':continue
            relative = src.relative_to(folder)
            dest = DEST_FIG / post['slug'] / relative
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dest)


def render_legacy_shortcodes(source):
    """Preserve basic highlights and line breaks from earlier Hugo writing."""
    for name, color in (("red", "danger"), ("#0099FF", "info")):
        source = source.replace('{{< span color="' + name + '" >}}',
                                '<span class="legacy-note-' + color + '">')
    source = source.replace('{{< /span >}}', '</span>')
    source = source.replace('{{< br >}}', '<br>')
    return source


def prepare_markdown(source, post):
    """Convert relative Markdown images to URLs for their generated copies."""
    slug = post['slug']
    def rewrite_local_image(match):
        filename = unquote(match.group('name'))
        if filename.startswith(('http:','https:','data:','../','/')):
            return match.group(0)
        target = (post['directory']/filename).resolve()
        if target.is_relative_to(post['directory']) and target.is_file():
            return match.group('start') + '../fig/' + slug + '/' + filename + match.group('end')
        return match.group(0)
    source = re.sub(r'(?P<start>!\[[^\]]*\]\()(?P<name>[^\s)]+)(?P<end>\))',
                    rewrite_local_image,source)
    source = re.sub(r'<!--\s*more\s*-->', '',source,flags=re.I)
    return render_legacy_shortcodes(source)


def generate_article_pages(posts, retired=None):
    DEST_ARTICLES.mkdir(parents=True, exist_ok=True)
    # Article URLs derive from the folder name; retired articles keep the same pattern.
    slugs = {post["slug"] for post in posts} | set(retired or ())
    # Remove stale output when a draft, post or entire section is removed.
    # Nothing outside the generated article directory is touched.
    for stale in DEST_ARTICLES.glob('*.html'):
        if stale.stem not in slugs:
            stale.unlink()
    for post in posts:
        cleaned = prepare_markdown(post['markdown'], post)
        content = markdown.markdown(
            cleaned,
            extensions=["fenced_code", "tables", "sane_lists", "toc", StrikethroughExtension()],
            output_format="html5",
        )
        back = '../' + section_for(post['section'])['page']
        page = f"""
        <div class="wrap article-shell">
          <a class="small-back" href="{back}">← 返回资料目录</a>
          <h1>{esc(post["title"])}</h1>
          <div class="article-byline">{f'作者：{esc(post["author"])} · ' if post["author"] else ''}{esc(post["date"])}</div>
          <article class="article-content">{content}</article>
          <div class="article-bottom"><a href="{back}">← 返回资料目录</a></div>
        </div>"""
        (DEST_ARTICLES / f'{post["slug"]}.html').write_text(layout(post["title"], page, depth=1), encoding="utf-8")


def normalize_posts(posts):
    return [
        {key: post[key] for key in ('title', 'date', 'category', 'author', 'tags', 'url', 'section')}
        for post in posts
    ]



def create_home(albums):
    # Independent sketch layers, rather than a large illustration as a background image.
    sketches = "".join(
        f'<img class="hero-sketch hero-sketch-{name}" src="./assets/hero-{name}.svg" alt="" loading="eager" draggable="false">'
        for name in ("trails", "axes", "laptop", "atom-burst", "flask", "planet", "mouse")
    )
    hero = f"""
    <section class="hero" aria-labelledby="site-title">
      <div class="hero-panel">
        <div class="hero-decor" aria-hidden="true">{sketches}</div>
        <div class="hero-center hero-story" data-hero-story>
          <div class="hero-expansion" aria-hidden="true">
            <span class="expansion-word"><span class="expansion-initial">D</span>epartment</span>
            <span class="expansion-word">for</span>
            <span class="expansion-word"><span class="expansion-initial">I</span>ntensive</span>
            <span class="expansion-word"><span class="expansion-initial">I</span>nstruction</span>
            <span class="expansion-word">of</span>
            <span class="expansion-word">Fundamental</span>
            <span class="expansion-word">Sciences</span>
          </div>
          <h1 id="site-title" aria-describedby="site-name-expansion"><span class="hero-acronym"><span class="hero-char">D</span><span class="hero-char">I</span><span class="hero-char">I</span></span><span class="hero-heading-rest"> 的博客</span></h1>
          <p class="hero-slogan">A place for dreams and dreaming</p>
          <span id="site-name-expansion" class="visually-hidden">DII: Department for Intensive Instruction of Fundamental Sciences</span>
        </div>
      </div>
    </section>"""
    # Show only the three newest events, sorted by the dates in index.md.
    featured = "".join(
        f'<a class="feature-album" href="./albums/{esc(item["id"])}.html">'
        f'<img src="{esc(item["images"][0])}" alt="" loading="lazy">'
        f'<span>{esc(item["title"])}</span></a>'
        for item in albums[:3]
    )
    below = f"""
    <section class="wrap home-section" aria-labelledby="latest-heading">
      <div class="section-heading"><h2 id="latest-heading">最近活动</h2><a href="./photos.html">全部相册 ↗</a></div>
      <div class="home-albums">{featured}</div>
    </section>"""
    return layout("首页", hero + below, current="home",
                  top_banner=render_home_announcement(PROJECT))


def read_json(filename):
    return json.loads((HERE / filename).read_text(encoding="utf-8"))


def book_card(entry):
    cover = entry['cover']
    href = entry.get('pdf') or entry.get('public_url')
    title = esc(entry['title'])
    picture = f'<img src="{esc(cover)}" alt="{title}封面" loading="lazy">'
    if href:
        open_link = (f'<a class="book-cover" href="{esc(href)}" target="_blank" rel="noopener">{picture}</a>')
        text = f'<h3><a href="{esc(href)}" target="_blank" rel="noopener">{title}</a></h3>'
    else:
        open_link = f'<span class="book-cover book-cover-unavailable">{picture}</span>'
        text = f'<h3>{title}</h3><p class="book-not-public">资源暂未开放</p>'
    return f'<article class="book-item">{open_link}{text}</article>'


def archive_listing(section, posts):
    """Generic searchable list used by every current/future article section."""
    categories = list(dict.fromkeys(post['category'] for post in posts))
    filters = ['全部', *[name for name in categories if name!='其他']]
    buttons = ''.join(
        f'<button class="filter{ " active" if i==0 else ""}" data-filter="{esc(name)}"'
        f' aria-pressed="{str(i==0).lower()}">{esc(name)}</button>'
        for i,name in enumerate(filters)
    )
    return f"""<section class="index-section" aria-label="{esc(section['list_title'])}"
         data-archive="{esc(section['id'])}" data-index="./sections/{esc(section['id'])}.json">
      <div class="section-heading"><h2>{esc(section['list_title'])}</h2></div>
      <div class="archive-toolbar">
        <div class="archive-tabs" role="group" aria-label="文章分类">{buttons}</div>
        <label class="archive-search"><span class="visually-hidden">搜索文章</span>
          <input class="archive-search-input" type="search" placeholder="搜索文章"></label>
      </div>
      <div class="archive-list"></div>
      <p class="visually-hidden archive-count" aria-live="polite"></p>
    </section>"""


def missing_materials(kind):
    """Full-page-friendly empty state reused across the three resource areas.

    The homepage is deliberately not modified; this component belongs only
    to its corresponding inner section when no resource is available.
    """
    folders = {
        'handbooks': (
            '手册', 'content/handbooks/', 'missing-handbooks-dino.svg',
            '一只戴眼镜的小恐龙，抱着装有文档的文件夹，旁边有指路牌和指南'),
        'textbooks': (
            '教材', 'content/textbooks/', 'missing-textbooks-dino.svg',
            '一只戴眼镜的小恐龙抱着打开的教材，周围是书本、铅笔和科学草图'),
        'album': (
            '相册', 'content/album/', 'missing-album-dino.svg',
            '一只戴眼镜的小恐龙拿着相机，身旁放着照片和相框'),
    }
    label, folder, illustration, description = folders[kind]
    return f"""<section class="resource-missing" aria-label="{label}资料尚未配置">
      <img class="resource-missing-art" src="./assets/{illustration}"
           alt="{description}" width="520" height="360">
      <h2>看来你缺少了一些必要材料哦</h2>
      <p class="resource-missing-subtitle">只有源代码是不可以的！</p>
      <span class="resource-missing-rule" aria-hidden="true"></span>
      <p class="resource-missing-hint">请把相应的{label}资料补充到服务器上的<br>
        <code>{folder}</code> 目录中，再重新构建网站。</p>
    </section>"""


def handbook_feature():
    entries = read_json('handbooks.json')
    if not entries:
        return missing_materials('handbooks')
    years = sorted({e['year'] for e in entries if e['year'].isdigit()},reverse=True)
    parts = []
    for year in years:
        this_year = sorted((e for e in entries if e['year']==year),
                           key=lambda e:(0 if e['kind']=='保研' else 1,e['title']))
        cards = ''.join(book_card(e) for e in this_year)
        parts.append(f'<section class="year-section"><h2 class="year-heading"><span>{year}</span></h2>'
                     f'<div class="book-row">{cards}</div></section>')
    other = [e for e in entries if e['year'] not in years]
    if other:
        parts.append('<section class="year-section"><h2 class="year-heading"><span>其他手册</span></h2>'
                     '<div class="book-row">'+''.join(book_card(e) for e in other)+'</div></section>')
    return f'<div class="year-list">{"".join(parts)}</div>'


def textbook_feature():
    books = read_json('textbooks.json')
    if not books:
        return missing_materials('textbooks')
    subjects = list(dict.fromkeys(item['subject'] for item in books))
    groups = []
    for subject in subjects:
        cards = ''.join(book_card(e) for e in books if e['subject']==subject)
        groups.append(f'<section class="subject-section"><h2>{esc(subject)}</h2>'
                      f'<div class="book-row">{cards}</div></section>')
    return f'<div class="subject-groups">{"".join(groups)}</div>'


def create_article_section(section, posts):
    own = [post for post in posts if post['section']==section['id']]
    description = (f'<p class="section-intro">{esc(section["description"])}</p>'
                   if section['description'] else '')
    feature = ''
    if section['feature']=='handbooks':
        feature = handbook_feature()
        missing = not read_json('handbooks.json')
    elif section['feature']=='textbooks':
        feature = textbook_feature()
        missing = not read_json('textbooks.json')
    else:
        missing = False
    # Missing resources occupy the whole content area. Keep the section
    # heading and navigation but hide article listings until configured.
    if missing:
        return layout(section['title'],
            f'<div class="wrap inner-page resource-missing-page">'
            f'<div class="page-heading"><h1>{esc(section["title"])}</h1></div>'
            f'{feature}</div>',current=section['id'])
    if section['list_style']=='simple':
        listing = ''.join(f'<a class="study-article" href="{esc(post["url"])}">'
                          f'<strong>{esc(post["title"])}</strong><span aria-hidden="true">↗</span></a>'
                          for post in own)
        articles = (f'<section class="index-section"><div class="section-heading"><h2>{esc(section["list_title"])}</h2></div>'
                    f'<div class="study-articles" data-static-section="{esc(section["id"])}">{listing}</div></section>')
    else:
        articles=archive_listing(section,own)
    return layout(section['title'],
                  f'<div class="wrap inner-page"><div class="page-heading">'
                  f'<h1>{esc(section["title"])}</h1></div>{description}{feature}{articles}</div>',
                  current=section['id'])


def create_photos(albums):
    """Album timeline: year groups newest first, preserving current photo cards."""
    if not albums:
        body = (f'<div class="wrap inner-page resource-missing-page">'
                f'<div class="page-heading"><h1>活动相册</h1></div>'
                f'{missing_materials("album")}</div>')
    else:
        years = []
        # build_albums() already orders by date descending; groupby keeps
        # the existing within-year order, including dates with no day/month.
        for year, entries in groupby(albums, key=lambda item: item['date'][:4]):
            items = []
            for album in entries:
                images = album['images'][:3]
                cards = ''.join(
                    f'<span class="stack-photo stack-{i+1}"><img src="{esc(pic)}" alt="" loading="lazy"></span>'
                    for i, pic in enumerate(images)
                )
                items.append(f"""<a class="album-tile" href="./albums/{esc(album['id'])}.html">
                    <span class="photo-stack" aria-hidden="true">{cards}</span>
                    <span class="album-title">{esc(album['title'])}</span>
                </a>""")
            years.append(
                f'<section class="year-section album-year" aria-label="{esc(year)}年活动">'
                f'<h2 class="year-heading"><span>{esc(year)}</span></h2>'
                f'<div class="album-grid">{"".join(items)}</div></section>'
            )
        body = (f'<div class="wrap inner-page">'
                f'<div class="page-heading"><h1>活动相册</h1></div>'
                f'<div class="album-years">{"".join(years)}</div></div>')
    return layout("活动相册", body, current="photos")


def create_album_pages(albums):
    destination = HERE / "albums"
    destination.mkdir(parents=True, exist_ok=True)
    active_ids = {album["id"] for album in albums}
    for previous in destination.glob("*.html"):
        if previous.stem not in active_ids:
            previous.unlink()
    for album in albums:
        photos = "".join(
            f'<img src="../{esc(image.removeprefix("./"))}" alt="{esc(album["title"])}，照片 {i}" loading="lazy">'
            for i, image in enumerate(album["images"], 1)
        )
        about = (f'<div class="album-description">{album["description_html"]}</div>'
                 if album.get("description_html") else "")
        body = f"""<div class="wrap inner-page">
            <a class="small-back" href="../photos.html">← 活动相册</a>
            <div class="page-heading album-heading"><h1>{esc(album["title"])}</h1></div>
            {about}
            <div class="album-photos">{photos}</div>
        </div>"""
        (destination / (album["id"] + ".html")).write_text(
            layout(album["title"], body, current="photos", depth=1),
            encoding="utf-8"
        )


def main():
    global SECTIONS, ARTICLES, HERE, DEST_ARTICLES, DEST_FIG, DEST_FILES
    final_dir = PROJECT / 'dist'
    HERE = PROJECT / '.site-build-staging'
    DEST_ARTICLES = HERE / 'articles'
    DEST_FIG = HERE / 'fig'
    DEST_FILES = HERE / 'files'
    # Build in isolation, then publish only after every input validates.
    # Old tracked GitHub Pages output survives a failed render intact.
    if HERE.exists():
        shutil.rmtree(HERE)
    HERE.mkdir(parents=True)
    shutil.copy2(SOURCE_DIR / 'app.js', HERE / 'app.js')
    shutil.copy2(SOURCE_DIR / 'styles.css', HERE / 'styles.css')
    shutil.copytree(SOURCE_DIR / 'assets', HERE / 'assets')
    SECTIONS = load_sections()
    all_posts = article_data()
    retired = retired_articles()
    known = {p['slug'] for p in all_posts}
    if unknown := (retired.keys() - known):
        raise ValueError(f'Retired article slugs do not exist: {sorted(unknown)}')
    posts = [p for p in all_posts if p['slug'] not in retired]
    ARTICLES = posts
    albums = build_albums(PROJECT, HERE)
    textbooks = build_textbooks(PROJECT, HERE)
    handbooks = build_handbooks(PROJECT, HERE)
    (HERE / 'legacy.json').write_text(
        json.dumps(normalize_posts(posts),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # The generic front-end archive fetches only its own section's data.
    feeds = HERE / 'sections'
    feeds.mkdir(exist_ok=True)
    live_names = {section['id']+'.json' for section in SECTIONS}
    for outdated in feeds.glob('*.json'):
        if outdated.name != '.pages.json' and outdated.name not in live_names:
            outdated.unlink()
    for section in SECTIONS:
        own = [post for post in posts if post['section']==section['id']]
        (feeds/(section['id']+'.json')).write_text(
            json.dumps(normalize_posts(own),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    generate_article_pages(posts, retired)
    create_retired_article_redirects(retired, all_posts)
    import_article_figures(posts)
    DEST_FILES.mkdir(exist_ok=True)
    create_album_pages(albums)
    pages = {
        'index.html':create_home(albums),
        'photos.html':create_photos(albums),
    }
    for section in SECTIONS:
        pages[section['page']] = create_article_section(section,posts)
    # Preserve a manifest of the *section* files this generator owns. When a
    # section is removed, remove only its stale generated landing page.
    manifest = HERE/'sections'/'.pages.json'
    try:
        previous = json.loads(manifest.read_text(encoding='utf-8'))
    except (FileNotFoundError,json.JSONDecodeError):
        previous = []
    live = [section['page'] for section in SECTIONS]
    for page in previous:
        if page not in live and re.fullmatch(r'[a-z0-9][a-z0-9_-]*\.html',page):
            (HERE/page).unlink(missing_ok=True)
    manifest.write_text(json.dumps(live,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name, body in pages.items():
        (HERE/name).write_text(body,encoding='utf-8')
    error_page = layout('页面未找到',
        '<div class="wrap inner-page"><h1>页面未找到</h1>'
        '<p>原链接可能已经调整。可以返回文章栏目继续浏览。</p>'
        '<p><a href="./index.html">返回首页</a></p></div>')
    (HERE/'404.html').write_text(error_page,encoding='utf-8')
    # Replace the generated tree after success without losing a working site on errors.
    backup = PROJECT / '.site-build-backup'
    if backup.exists():
        shutil.rmtree(backup)
    if final_dir.exists():
        final_dir.rename(backup)
    try:
        HERE.rename(final_dir)
    except Exception:
        if backup.exists(): backup.rename(final_dir)
        raise
    else:
        if backup.exists(): shutil.rmtree(backup)
    print(f'Built intranet site in {final_dir.relative_to(PROJECT)} (not version-controlled)')
    print(f'Built {len(pages)} index pages, {len(posts)} article pages, '
          f'{len(retired)} handbook redirects, {len(albums)} albums, '
          f'{len(textbooks)} textbooks and {len(handbooks)} handbooks '
          f'across {len(SECTIONS)} article sections.')


if __name__=='__main__':
    main()
