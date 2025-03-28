from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import QRegExp

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("blue"))
        keyword_format.setFontWeight(QFont.Bold)

        keyword_patterns = [
            '\\bdef\\b', '\\bclass\\b', '\\bimport\\b', '\\bfrom\\b', '\\breturn\\b',
            '\\bif\\b', '\\belif\\b', '\\belse\\b', '\\bwhile\\b', '\\bfor\\b',
            '\\bin\\b', '\\bnot\\b', '\\band\\b', '\\bor\\b', '\\bpass\\b',
            '\\bbreak\\b', '\\bcontinue\\b', '\\btry\\b', '\\bexcept\\b', '\\bwith\\b',
            '\\bas\\b', '\\bassert\\b', '\\blambda\\b', '\\bNone\\b', '\\bTrue\\b', '\\bFalse\\b'
        ]

        self.highlighting_rules = [(QRegExp(pat), keyword_format) for pat in keyword_patterns]

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("darkGreen"))
        self.highlighting_rules.append((QRegExp("\".*\""), string_format))
        self.highlighting_rules.append((QRegExp("\'.*\'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("darkGray"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegExp("#.*"), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)