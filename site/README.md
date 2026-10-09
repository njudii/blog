# 正式网站生成器

`site/` 存放网页代码：`build-site.py` 负责按文章文件夹名自动生成栏目、文章网址与主页；`album_builder.py`、`handbook_builder.py`、`textbook_builder.py` 处理三个资源区；`markdown_extensions.py` 补充旧文章使用的 `~~删除线~~` 语法；`app.js` 和 `styles.css` 维护网页交互与布局。

运行 `make build`，构建器读取 `../content/`，先写入临时生成目录，全部成功后再替换 `../dist/`。不需要任何部署服务，不会提交或上传文件。

完整站点只能由内网服务器上的资料生成。`content/album/`、`content/handbooks/` 和 `content/textbooks/` 在 Git 仓库中都只保留 `.gitkeep`；当内网服务器填充相册图片及 `index.md` 或手册/教材的 `index.md` 与 `book.pdf` 后，构建器自动发现并显示。缺少这些子文件夹时，网站正常显示各栏目的空资料区。

修改页面设计应编辑本目录源码，编辑文章或相册应在 `../content/`；不要直接编辑 `../dist/`。详细操作见根目录 `README.md`。

资源缺失时由 `build-site.py` 的 `missing_materials()` 生成文案样式统一但**插图不同**的三个空状态：`assets/missing-handbooks-dino.svg`（文件夹与指南）、`assets/missing-textbooks-dino.svg`（教材与书堆）、`assets/missing-album-dino.svg`（相机与照片）。样式在 `styles.css` 中的 `.resource-missing`。三个栏目根据各自的 JSON 是否为空分别判断；活动相册没有可用照片时也可正常构建。不要改动首页的空相册处理，待视觉方案明确后再考虑。

文章文件夹标识必须是小写 `kebab-case`，不需要配置 `slug`。构建后的文章地址统一为 `articles/<文件夹名>.html`，不额外生成旧版 Hugo `/post/` 等网址。`retired-articles.json` 只维护五篇已收录文章与手册 PDF 的关系，**不是网址映射表**。

首页公告：`announcement.py` 读取 `content/announcement.yaml`，支持启用开关、一句话与可选超链接。仅在首页导航下方渲染，不固定悬浮。未配置真实链接前请保持 `enabled: false`。

相册总览：`build-site.py` 的 `create_photos()` 按 `albums.json` 的日期年份分组，仍使用原有叠放照片卡片及小恐龙空状态；首页 `create_home()` 的最近三张相册卡片未改动。
