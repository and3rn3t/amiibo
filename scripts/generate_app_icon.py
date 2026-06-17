#!/usr/bin/env python3
"""Generate a branded macOS app icon for amiibo-flipper."""

from __future__ import annotations

import os
from pathlib import Path
import sys

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QGuiApplication,
    QColor,
    QFont,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)

ICON_SIZE = 1024
OUTPUT_PATH = Path("assets/icon.png")


def main() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    image = QImage(ICON_SIZE, ICON_SIZE, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    rect = QRectF(32, 32, ICON_SIZE - 64, ICON_SIZE - 64)
    radius = 220.0

    background = QLinearGradient(rect.topLeft(), rect.bottomRight())
    background.setColorAt(0.0, QColor("#0c171d"))
    background.setColorAt(0.45, QColor("#12303b"))
    background.setColorAt(1.0, QColor("#1b6f7d"))

    shell = QPainterPath()
    shell.addRoundedRect(rect, radius, radius)
    painter.fillPath(shell, background)

    outline_pen = QPen(QColor("#58b1c2"))
    outline_pen.setWidth(12)
    painter.setPen(outline_pen)
    painter.drawPath(shell)

    glow = QPainterPath()
    glow.addRoundedRect(QRectF(96, 96, 832, 832), 180, 180)
    painter.fillPath(glow, QColor(255, 255, 255, 16))

    stripe = QLinearGradient(QPointF(128, 168), QPointF(820, 760))
    stripe.setColorAt(0.0, QColor("#21d0ea"))
    stripe.setColorAt(1.0, QColor("#78ffd4"))
    painter.setPen(Qt.PenStyle.NoPen)

    ribbon = QPainterPath()
    ribbon.moveTo(184, 676)
    ribbon.cubicTo(328, 508, 470, 352, 612, 224)
    ribbon.cubicTo(676, 164, 766, 150, 848, 176)
    ribbon.lineTo(848, 270)
    ribbon.cubicTo(752, 242, 670, 264, 606, 326)
    ribbon.cubicTo(488, 438, 370, 566, 246, 722)
    ribbon.closeSubpath()
    painter.fillPath(ribbon, stripe)

    chip_pen = QPen(QColor("#dff7fb"))
    chip_pen.setWidth(28)
    chip_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(chip_pen)
    painter.drawLine(276, 280, 276, 492)
    painter.drawLine(392, 280, 392, 492)
    painter.drawLine(508, 280, 508, 492)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#dff7fb"))
    painter.drawRoundedRect(QRectF(228, 468, 352, 190), 56, 56)

    letter_font = QFont("Avenir Next", 250, QFont.Weight.Black)
    painter.setFont(letter_font)
    painter.setPen(QColor("#0e242c"))
    painter.drawText(QRectF(248, 408, 308, 290), Qt.AlignmentFlag.AlignCenter, "A")

    wordmark_font = QFont("Avenir Next", 72, QFont.Weight.Bold)
    wordmark_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
    painter.setFont(wordmark_font)
    painter.setPen(QColor("#ecf7fa"))
    painter.drawText(QRectF(142, 768, 736, 120), Qt.AlignmentFlag.AlignCenter, "FLIPPER")

    painter.end()
    image.save(str(OUTPUT_PATH))
    app.quit()


if __name__ == "__main__":
    main()
