from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import QRegExp

class JsHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("blue"))
        keyword_format.setFontWeight(QFont.Bold)

        keywords = [
            'var', 'let', 'const', 'function', 'return', 'if', 'else', 'for', 'while',
            'do', 'switch', 'case', 'break', 'continue', 'try', 'catch', 'finally',
            'throw', 'new', 'this', 'typeof', 'instanceof', 'in', 'of', 'null', 'true', 'false'
        ]

        self.highlighting_rules = [(QRegExp(f"\\b{kw}\\b"), keyword_format) for kw in keywords]

        # String
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("darkGreen"))
        self.highlighting_rules.append((QRegExp("\".*\""), string_format))
        self.highlighting_rules.append((QRegExp("\'.*\'"), string_format))

        # Comment
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("darkGray"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegExp("//[^\"]*"), comment_format))
        self.highlighting_rules.append((QRegExp("/\*.*\*/"), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)
