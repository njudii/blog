+++
title = "Readme"
date = 2019-12-29T16:34:16+08:00
postauthor = ["本文作者"]
draft = false
+++

这里的文本会出现在首页，即“阅读全文”之前。

<!--more-->

此处向下是正文文本。

## 正文标题请从第2级开始

### 这是第3级标题

#### 这是第4级标题

下面是一个 `` itemize `` 列表（你也可以把 `` - `` 换成 `` 1. `` 来得到一个 `` enumerate `` 列表）：

- 如要插入链接，请这样使用：你可以在[这里](https://guides.github.com/features/mastering-markdown/)学习使用markdown。如果要插入站内链接，如 `` innerlinks `` 里的网页，可以这样使用：[站内链接](/blog/innerlinks/readme/)。
- 如要插图，请把图片放到 `` fig `` 文件夹，插图时这样使用：
   ![图片名](/blog/fig/name.png)
- 如要插入引用文字或小段注解，请这样使用：
   > 这是引用文字，这是引用文字，这是引用文字，这是引用文字，这是引用文字，这是引用文字，这是引用文字，这是引用文字，这是引用文字，这是引用文字，这是引用文字，这是引用文字。
- 如要插入代码，请这样使用：
   ```python
   import numpy as np
   import matplotlib.pyplot as pl
   x = np.linspace(0, 2*np.pi, 100)
   y = np.sin(x)
   pl.plot(x, y)
   ```
- 如果要使用一些html语法，比如改变字体颜色、居中对齐等等，请自行阅读Hugo的 `` shortcodes `` 的文档（这也是我吐槽Hugo的一点...）。这里只给几个示例：
   - 字体颜色：{{< span color="red" >}} 这里是红色 {{< /span >}}
   - 居中对齐：

{{< p text-align="center" >}} 这里是居中文字 {{< /p >}}

这个`` --- ``表示画一条水平线，正文内容止步于此。

---
