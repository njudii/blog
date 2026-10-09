"""Markdown features used by legacy posts and new student submissions."""
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor


class StrikethroughExtension(Extension):
    """Support ~~deleted text~~ without affecting fenced or inline code.

    Python-Markdown does not interpret this GFM-style syntax by default.
    A real inline processor keeps nested bold/italic working, unlike a
    regex-based substitution on the resulting HTML string.
    """

    def extendMarkdown(self, md):
        # The paired (~~) captures the delimiter; SimpleTagInlineProcessor
        # expects group 2 to contain the text. A single leading escape slash
        # prevents accidental formatting of literal Markdown characters.
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(
                r'(?<![\\~])(~~)(?!~)(.+?)(?<![\\~])\1(?!~)',
                'del',
            ),
            'strikethrough',
            60,
        )
