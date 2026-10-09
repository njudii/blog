# DII 文章投稿与 Markdown 维护指南

每篇文章是 `content/articles/<栏目>/<文章标识>/index.md`，配图可以直接与它放在同一个文件夹，不必另建 `fig` 目录。

例如，向文学创作栏目投稿：

```text
content/articles/creative/autumn-letter/
  index.md
  photo.jpg
```

`index.md` 示例：

```markdown
---
title: "秋天的一封信"
date: "2026-10-08"
author: "作者或笔名"
category: "散文"
tags: ["随笔"]
draft: false
---

这是一段正文。

![照片](photo.jpg)

## 第二级标题

可以使用 **加粗**、*斜体*、~~删除线~~、[链接](https://example.com) 和有序/无序列表。
```

- 放在 `creative/` 即属于文学栏目，放在 `experience/` 即属于升学经验；`category`/`tags` 只控制栏目内筛选和搜索。
- 未完成时设 `draft: true`，草稿不生成正文页面，也不显示在导航列表中。
- 图片、附件放在同一个文章文件夹。后续替换图片时不用修改生成页面。
- 历史文档仍支持 `+++` TOML 元数据，但站内链接统一指向生成后的 `articles/<文件夹名>.html`；在文章正文中链接另一篇文章可写 `[参考文章](./另一篇文章名.html)`。图片仍用相对路径 `![图片](图片.jpg)`。
- 文学作品的期号可写 `series: "..."`、`issue: 1` 留作元数据，**当前暂不自动制作期刊合辑**；后续如果确定期刊展示样式，再单独实现这一功能。
- 文章文件夹名采用**小写英文和连字符**，如 `physics-course-tips`，避免大写、下划线或作者缩写；不要随意改动已发布文件夹名，因为它直接决定 `/articles/physics-course-tips.html` 这样的新网址。

新增栏目参考仓库根目录 `README.md` 的 `_section.md` 示例。使用 `make build` 编译；`make build` 测试。

**删除线写法：** `~~要删除的文字~~`（左右各两个 `~`）；也能在加粗里使用 `**文字~~划掉~~文字**`。连续四个 `~~~~` 单独成行在 Markdown 中表示代码围栏，不是删除线。
