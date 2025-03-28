from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import QRegExp

class HtmlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        # HTML Tag
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("darkBlue"))
        tag_format.setFontWeight(QFont.Bold)
        self.tag_pattern = QRegExp("<[^>]+>")

        # Attribute
        attr_format = QTextCharFormat()
        attr_format.setForeground(QColor("brown"))
        self.attr_pattern = QRegExp("\\b\w+(?=\\=)")

        # Attribute Value
        value_format = QTextCharFormat()
        value_format.setForeground(QColor("darkGreen"))
        self.value_pattern = QRegExp("\"[^\"]*\"|\'[^\']*\'")

        # Comment
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("gray"))
        comment_format.setFontItalic(True)
        self.comment_pattern = QRegExp("<!--[^>]*-->")

        self.highlighting_rules = [
            (self.tag_pattern, tag_format),
            (self.attr_pattern, attr_format),
            (self.value_pattern, value_format),
            (self.comment_pattern, comment_format)
        ]

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)