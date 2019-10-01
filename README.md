## NJUDII的博客仓库

**重要，请认真阅读**

1. 软件需求
   + hugo >= 0.41
   + git

2. 安装完上述软件后：
   ```shell
   git clone git@github.com:njudii/blog.git
   cd blog/ # 以下称为根目录
   ```
   （注：这个仓库使用`` docs ``目录作为GitHub-Pages。）

3. 在根目录下使用`` hugo new post/xxx.md ``来新建一个文件（为保证格式统一，请不要把别的md文件直接复制到`` content/post/ ``里）。然后编辑`` content/post/xxx.md ``文件。(参考下面的“Hugo的用法”)

   使用`` hugo server ``启动本地浏览器预览。编辑完成，预览无误后，运行`` deploy.sh ``即可部署到网页(当然如果不是Linux系统，你也可以手动执行里面的内容)。

4. 如果你**不**是该repo的唯一编辑者， **每次编辑前要pull！编辑后要push！**，即不要造成冲突。

5. 目录结构为(有的目录没有，没关系，如果需要可以自己创建)：
   ```
   .
   ├── README.md
   ├── config.toml     # 博客站点的配置文件，基本不用改
   ├── deploy.sh       # 部署到GitHub的脚本
   ├── archetypes/     # 文章模板
   ├── content/        # 博客文章内容
   │   ├── about/      # about页面，可以修改
   │   ├── archives/   # 用来生成归档，不用修改
   │   ├── fig/        # 存放文章插图，插图方式为![](/blog/fig/xxx.png)
   │   ├── innerlinks/ # 放一些杂物，内链页面等等
   │   └── post/       # 博客文章的文件，主要工作就在这
   ├── docs/           # GitHub-Pages
   ├── files/          # 放大文件(~>5M)，但是强烈不建议用GitHub放大文件！能写成文字的尽量写文字
   ├── public/         # 不知道什么用
   ├── resources/      # 同上
   ├── static/         # 官方说用来放大文件，但我没用(我用了上面那个`` files ``)
   └── themes/         # 放博客主题，主要是~~前端切图仔~~的工作，基本不用改，除非你知道这是什么
       └── maupassant/
   ```

## 附加：Hugo的简单用法

`` hugo `` 和 `` hexo `` 一样是个静态博客网页生成软件，优点是轻便。

注： 如果你要全新建立一个博客（不像这里的repo），输入 `` hugo new site xxx ``，然后cd进入你博客的根目录（比如这里的`` blog/ ``）。

以下操作都默认在博客根目录执行。

1. 修改配置文件`` config.toml ``中相关部分

1. 新建一篇文章：

   ```shell
   hugo new post/xxx.md
   ```
   编辑那个xxx.md，写入你想写的内容，保存退出。

1. 编辑文章
   1. 开头
   
      每一篇新建的文章的开头都形如：
      ```
      ---
      title: "标准化考试专题(T/G/I/Sub)"
      date: 2019-07-19T00:00:00
      tags: [TOEFL, GRE, Sub]
      categories: ["出国"]
      draft: false
      ---
      ```
      每个条目的作用可以顾名思义。这里建议`` categories ``只写一个，`` tags ``可以根据自己的需求写。
   2. 中间
   
      `` <!--more--> ``是用来分割文章预览与正文的，写在其之前的文字会出现在首页。可以参考现有的文章。文章的段落标题分级从二级标题`` ## ``开始。
   3. 结尾
   
      按照模板，结尾会有一个`` <p style="text-align:center">~~By: ~~</p> ``，只要把作者的署名（要问作者的意见）写到`` By: ``后面即可。

1. 选定主题：

   到hugo的[主题网站](https://themes.gohugo.io/)选一个你喜欢的主题，并按说明安装。本博客的主题是[`` maupassant ``](https://github.com/rujews/maupassant-hugo)。
   > 本repo已经安装好了，这一步不用操作。

1. 本地预览：

   ```shell
   hugo server
   ```
   执行过这条命令后有类似如下的输出：
   ```
   Web Server is available at http://localhost:1313/ (bind address 127.0.0.1)
   Press Ctrl+C to stop
   ```
   打开浏览器就可以看到本地预览效果了。

1. 部署到github：

   ```shell
   hugo
   ```
   执行完，根目录下你会有一个`` public ``文件夹，把里面的东西push到你已经开启[`` GitHub Pages ``](https://pages.github.com/)功能的repo里就可以了。
   > 本repo已经设置好了，这一步只要运行`` deploy.sh ``。
