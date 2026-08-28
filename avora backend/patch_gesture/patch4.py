# 6. paintEvent - add close indicator call at the end
replace_once(
    """        self.draw_body_details(
            painter,
            y,
        )

    # ========================================================
    # HEAD TRANSFORM
    # ========================================================""",
    '        self.draw_body_details(\n'
    '            painter,\n'
    '            y,\n'
    '        )\n'
    '\n'
    '        # Draw the close (X) indicator on top - fixed at bottom-center\n'
    '        self._draw_close_indicator(painter)\n'
    '\n'
    '    # ========================================================\n'
    '    # CLOSE INDICATOR\n'
    '    # ========================================================\n'
    '\n'
    '    def _draw_close_indicator(self, painter):\n'
    '        """Draw the close (X) indicator fixed at the window bottom-center."""\n'
    '        if not self.close_x_visible:\n'
    '            return\n'
    '\n'
    '        cx = self.width() / 2.0\n'
    '        radius = self.X_BASE_RADIUS * self.close_x_scale\n'
    '        cy = self.height() - 45.0\n'
    '        cy = min(cy, self.height() - radius - 6.0)\n'
    '\n'
    '        sigma = max(0.0, min(1.0, self.close_x_opacity))\n'
    '        if sigma <= 0.0:\n'
    '            return\n'
    '\n'
    '        painter.save()\n'
    '        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)\n'
    '\n'
    '        # Outer glow\n'
    '        glow = QRadialGradient(QPointF(cx, cy), radius * 1.4)\n'
    '        glow.setColorAt(0.0, QColor(245, 82, 82, int(90 * sigma)))\n'
    '        glow.setColorAt(1.0, QColor(245, 82, 82, 0))\n'
    '        painter.setBrush(QBrush(glow))\n'
    '        painter.setPen(Qt.PenStyle.NoPen)\n'
    '        painter.drawEllipse(QPointF(cx, cy), radius * 1.4, radius * 1.4)\n'
    '\n'
    '        # Solid circle\n'
    '        circle_fill = QRadialGradient(QPointF(cx - radius * 0.2, cy - radius * 0.3), radius)\n'
    '        circle_fill.setColorAt(0.0, QColor(255, 103, 103, int(235 * sigma)))\n'
    '        circle_fill.setColorAt(1.0, QColor(235, 60, 70, int(225 * sigma)))\n'
    '        painter.setBrush(QBrush(circle_fill))\n'
    '        painter.setPen(QPen(QColor(255, 170, 170, int(160 * sigma)), 2.0))\n'
    '        painter.drawEllipse(QPointF(cx, cy), radius, radius)\n'
    '\n'
    '        # X mark\n'
    '        pen_width = max(2.5, radius * 0.16)\n'
    '        painter.setPen(QPen(QColor(255, 255, 255, int(250 * sigma)), pen_width,\n'
    '                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))\n'
    '        off = radius * 0.38\n'
    '        painter.drawLine(QPointF(cx - off, cy - off), QPointF(cx + off, cy + off))\n'
    '        painter.drawLine(QPointF(cx + off, cy - off), QPointF(cx - off, cy + off))\n'
    '\n'
    '        painter.restore()\n'
    '\n'
    '    # ========================================================\n'
    '    # HEAD TRANSFORM\n'
    '    # ========================================================',
    "paintEvent",
)

# Fix: filter out count entries before validation
status_entries = [r for r in report if 'count=' not in r]

# Write back
if all('OK' in r for r in status_entries):
    with open(PATH, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print("ALL EDITS APPLIED SUCCESSFULLY")
else:
    print("SOME EDITS FAILED:")
    for r in report:
        print("  -", r)
    sys.exit(1)