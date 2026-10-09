# 活动相册：添加、修改与自动生成

**隐私说明：活动相册完全不上传 GitHub。** `content/album/` 在仓库中仅保留 `.gitkeep`；`index.md` 和全部原始照片都在内网服务器或本地工作区，由 `.gitignore` 排除。新克隆出来的仓库不会包含任何旧相册，必须自行安全备份、复制回服务器。生成的 `dist/`（含相册照片）同样不得上传公开仓库。

以后每个相册只需要一个文件夹：**一个 `index.md` + 若干张照片**，不需要再编辑 JSON、HTML 或手动压缩照片。

例如，新增活动时，在 `content/album/` 下创建目录 `2025_winter_kuangkengongyuan/`，结构如下：

```text
content/album/
  2025_winter_kuangkengongyuan/
    index.md
    照片A.jpg
    照片B.jpg
    ...
```

`index.md` 最简单的内容：

```markdown
---
title: "2025·汤山方山矿坑公园"
date: "2025"
---
```

`title` 是网页上显示的相册名，`date` 用来自动按时间倒序排序。最好填写真实活动日期，如 `2025-12-14`；暂时不知道具体日期时，可以只填 `2025` 或 `2025-12`，**不需要编造日期**。活动发生的具体日期确认后，改一行即可。

如需指定封面，可以额外写 `cover: "照片A.jpg"`；否则按文件名字母顺序自动取第一张。封面以及之后两张同时用于相册页的扑克牌式缩略图。如需给整个活动补充一段文字，在第二个 `---` 后直接写 Markdown 正文即可。图片支持 JPEG、PNG、WEBP、TIFF，照片的拍摄旋转信息会自动校正。

在 `blog/` 根目录运行：

```bash
python3 site/build-site.py
```

系统将扫描所有 `content/album/*/index.md`，自动整理、缩放、生成照片资源、相册总览页 `dist/photos.html` 及每个活动的独立网页 `dist/albums/文件夹名.html`。首页“最近活动”自动取日期最近的三项，无需单独管理。`dist/albums.json` 也是自动生成文件，**不要手工编辑**。

首次运行若缺少依赖：

```bash
python3 -m pip install markdown Pillow PyYAML
```

`content/album/` 下的原始照片不会被生成器修改，也不会被 Git 跟踪；请独立备份，并在内部访问控制、版权和肖像隐私许可范围内使用。相册文件夹名用于固定网页网址；创建后尽量不要改名，以免旧链接失效。

## 总览页面的年份分组

`photos.html` 会按 `date` 的年份将所有活动分组，年份从新到旧；同一年内也按日期新到旧。`date` 可以只写年份或月份，但同年排序更推荐完整 `YYYY-MM-DD`。首页仍只展示日期最新的三个活动，不受分组视觉的影响。
