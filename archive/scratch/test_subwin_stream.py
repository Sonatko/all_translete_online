import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
from PyQt6.QtWidgets import QApplication
from subtitle_window import SubtitleWindow

app = QApplication(sys.argv)
win = SubtitleWindow()
win.show()

print("Original sentences:", win._sentences)
win.update_streaming("Hello world", "Привет")
app.processEvents()
print("Sentences after 1:", win._sentences)
print("Widget 0:", win._text_widgets[0]._text)
print("Widget 1:", win._text_widgets[1]._text)

win.update_streaming("Hello world", "Привет мир")
app.processEvents()
print("Sentences after 2:", win._sentences)
print("Widget 0:", win._text_widgets[0]._text)
print("Widget 1:", win._text_widgets[1]._text)

win.close()
