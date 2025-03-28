from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import QRegExp

class CssHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        # Selector format
        selector_format = QTextCharFormat()
        selector_format.setForeground(QColor("blue"))
        selector_format.setFontWeight(QFont.Bold)
        self.selector_pattern = QRegExp("^[\w\.#][^{]+(?=\s*\{)")

        # Property format
        property_format = QTextCharFormat()
        property_format.setForeground(QColor("darkRed"))
        self.property_pattern = QRegExp("\b[a-zA-Z-]+(?=\s*:)\b")

        # Value format
        value_format = QTextCharFormat()
        value_format.setForeground(QColor("darkGreen"))
        self.value_pattern = QRegExp(":\s*[^;]+;")

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("gray"))
        comment_format.setFontItalic(True)
        self.comment_pattern = QRegExp("/\*[^*]*\*/")

        self.highlighting_rules = [
            (self.selector_pattern, selector_format),
            (self.property_pattern, property_format),
            (self.value_pattern, value_format),
            (self.comment_pattern, comment_format),
        ]

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)
