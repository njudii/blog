# DII 的博客

南京大学匡亚明学院学生博客。仓库只管理**文章、网站源代码和维护说明**。活动相册、手册和教材资料由内网服务器单独保存，在内网服务器使用 Python 生成静态 HTML；不使用 Hugo、GitHub Pages，也不提供自动部署程序。

## 结构

```text
content/
├── articles/                    正式文章，一篇一个目录（包含 index.md 和配图）
│   ├── experience/              升学经验
│   ├── study/                   学习资料
│   └── creative/                文学创作
├── album/                       GitHub 仅有 .gitkeep；相册照片及元数据由内网服务器提供
├── handbooks/                   仅 .gitkeep 在 GitHub；资料由内网服务器提供
└── textbooks/                   仅 .gitkeep 在 GitHub；资料由内网服务器提供
site/                            页面生成器、CSS/JS 和设计素材
maintainers/                     Markdown 投稿与活动相册维护说明
requirements.txt
Makefile
dist/                            静态网站生成结果（Git 忽略，不上传 GitHub）
```

`content/` 保存编辑内容；`site/` 保存网页模板、样式与构建脚本；`dist/` 是可以交给内网 HTTP 服务器的**纯静态文件目录**。请不要手工改 `dist/`，重新构建会覆盖它。

## 运行

要求 Python 3.11+，以及 `requirements.txt` 中的依赖。如果书籍/手册没有自定义封面，需要 Poppler 的 `pdftoppm` 提取 PDF 第一页。

```bash
python3 -m pip install -r requirements.txt
make build      # 生成 dist/，不会 push、上传或部署
make serve      # 浏览器打开 http://127.0.0.1:8848/
make clean      # 可选：删除本地生成的 dist/
```

在内网服务器上准备好资料后运行同一个 `make build` 即可。静态 Web 服务器的站点根目录指向 `dist/`，使用服务器侧访问控制限制访问；**不需要提交生成文件，也不需要把私有 PDF 上传 GitHub**。

## 首页公告栏

首页导航栏**下方**有一条独立的细公告条；它不会随滚动固定在屏幕上，其他栏目页也不会出现。公告内容只需编辑 [`content/announcement.yaml`](content/announcement.yaml)，不用修改 HTML：

```yaml
enabled: true
text: "网站改版意见征集中，欢迎填写问卷"
link_text: "前往填写"
url: "https://你实际使用的问卷网址"
```

目前因尚未填写真实问卷链接，默认是 `enabled: false`（隐藏）。将示例网址替换成真实地址后开启即可。`text` 是显示的一句话，`link_text` 是后方的短链接文字；若只想展示文字，`link_text` 和 `url` 都留空。活动报名时也可直接复用这个配置。修改后重新运行 `make build`。

## 活动相册按年份分组

活动相册总览页按 `content/album/<活动>/index.md` 里的 `date` **年份降序**分组，同年按已有的日期从新到旧排列，并保留照片叠放卡片。日期支持 `YYYY`、`YYYY-MM`、`YYYY-MM-DD`，建议尽量填写完整日期，以便同年活动排序更准确。首页最近三场活动的逻辑保持不变。

## 相册、手册、教材只在内网服务器保存

**三类资料都只放在服务器本地，不上传 GitHub**。手册/教材的 PDF、封面、`index.md`，以及相册的原始照片和 `index.md` 均被 `.gitignore` 忽略。仓库里三个目录各自只保留 `.gitkeep`（Git 不能直接记录完全空的文件夹）：

- `content/album/.gitkeep`
- `content/handbooks/.gitkeep`
- `content/textbooks/.gitkeep`

请单独备份这些资料，**不能通过重新克隆 GitHub 仓库恢复相册照片或 PDF**。内网服务器取得源代码后，把私有资料补入相同目录，再运行 `make build`。静态输出 `dist/` 含照片和 PDF，同样不能推送 GitHub。

服务器上将资料放在相同路径，例如：

```text
content/handbooks/
  baoyan-2016/
    index.md
    book.pdf
    cover.jpg                 可选
content/textbooks/
  higher-algebra-5/
    index.md
    book.pdf
    cover.png                 可选
```

手册的 `index.md`：

```yaml
---
title: "保研攻略"
year: "2016"
kind: "保研"
---
```

教材的 `index.md`：

```yaml
---
title: "高等代数（第五版）"
subject: "数学"
---
```

若同目录有 `cover.jpg`、`cover.jpeg`、`cover.png` 或 `cover.webp`，直接使用该图片；否则从 `book.pdf` 首页生成封面。完成的资料会生成在 `dist/files/handbooks/` 和 `dist/files/textbooks/`，网页也会自动列出对应条目并链接到 PDF。

**没有服务器资料也能构建。** 克隆仓库后，若手册、教材或活动相册没有可用内容，相应栏目页会显示三种不同场景的戴眼镜小恐龙（手册拿文件夹、教材读书、相册拿相机），以及「看来你缺少了一些必要材料哦 / 只有源代码是不可以的！」的大型提示。每个栏目单独判断，并告知需要补充的 `content/` 目录；补齐后重新运行 `make build` 即可恢复内容。首页的「最近活动」区域暂时保持现有逻辑，不额外处理空相册情况。每个手册/教材文件夹只有同时提供 `index.md` 和 `book.pdf` 才会被加入页面。

注意：不提交 Git 不等于解决版权问题。内网访问也应按资料授权范围设置账号、网络限制和日志管理，明确标为仅校内传阅的资料不能未经许可对校外开放。

## 投稿、新栏目与相册

在 `content/articles/<栏目>/<文章英文标识>/index.md` 写文章，配图放在同一个文件夹。栏目由所在目录决定，`category` 和 `tags` 只供栏目内筛选。旧 TOML `+++` 和新 YAML `---` 元数据都可使用。

**文章目录统一采用小写英文 kebab-case**，例如 `baoyan-application-tips`、`us-chemistry-phd-2020`、`physics-course-tips`：单词之间用 `-`，不允许大写、下划线、空格；名称应尽量体现文章主题，不要只写作者缩写或 `test1`。只有在申请季、教材版本等具有实际意义时才将年份放进名称。

构建器会自动用文章所在文件夹名生成 `/articles/<文件夹名>.html`，例如 `content/articles/experience/baoyan-application-tips/index.md` 对应 `dist/articles/baoyan-application-tips.html`。**不需要 `slug` 字段或手工 URL 映射。** 网址与目录名绑定，发布后改名会同时改变网址；若要改名，记得更新其他文章中的相关链接。

新建文章型栏目：在 `content/articles/interview/_section.md` 写入以下配置，再发表一篇正文：

```yaml
---
title: "人物访谈"
order: 25
list_title: "访谈记录"
---
```

构建器会自动生成该栏目的页面、导航、筛选和滚动位置恢复。没有正式文章的空栏目默认不进入导航。细节见 [`maintainers/markdown-guide.md`](maintainers/markdown-guide.md)。

相册（**只在服务器本地添加，GitHub 不保存这些文件**）：在 `content/album/<活动>/` 放 `index.md` 和照片，使用 `date: "YYYY-MM-DD"` 标记发生日期；首页按日期自动显示最近三场活动。详见 [`maintainers/album-guide.md`](maintainers/album-guide.md)。活动照片仍应经肖像与传播授权审查，不能因为是内网就忽略隐私。

## 其他说明

- 历史文章的文件夹已统一重命名为小写连字符格式，站点只使用新 URL，不再为 Hugo 旧地址单独生成兼容跳转。
- `site/retired-articles.json` 保留五篇已收入手册的旧文章与手册映射。如果服务器提供对应 PDF，旧文章可跳转到手册；否则显示说明页。
- 目前不设 GitHub Pages、Hugo、`deploy.sh` 或自动测试目录；构建器仍检查必要元数据和资源，不完整的书籍目录不会发布。
- `dist/` 是生成后的完整网站，可能包含仅内网可用的 PDF **和活动照片**，**严禁把它加入 Git 或复制到公共 Web 根目录**。
- `content/articles/` 中的文章、随文插图，以及 `site/assets/` 中的网站设计素材，仍属于源码仓库的一部分；本次隔离的是整套活动相册资料、手册和教材。
