# BoltPages

AKA. `Yet Another Pythonic Blog`

这是一个用纯 Python 实现的静态博客生成器归档仓库，保留了原项目的构建逻辑、模板系统和文章渲染能力，并对公开内容做了脱敏处理。

Features：高效缓存机制、webp图像压缩、数学公式支持（typst）、流程图支持（mermaid）、响应式设计、可配置的主题色、深色模式、代码高亮等

如果你想把它当作一个简单的静态博客生成器继续使用，可以参照下面的步骤：

1. 将`build.py`、`templates`复制到一个目录下，或者直接克隆本仓库并删除`posts`里的所有文章。
2. 安装依赖

    ```sh
    pip install mistune pygments jinja2 pillow python-frontmatter minify-html rich
    ```

    如果您需要使用数学渲染，请安装[typst](https://github.com/typst/typst)，这是一个rust编写的强大且快速的排版系统。

3. 运行`build.py`，生成的静态文件在`build`目录下。如果遇到了任何问题，请询问LLM。

更多玩法请自行阅读源码。欢迎任何建议和贡献。
