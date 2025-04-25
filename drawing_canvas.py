# drawing_canvas.py

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPolygonItem,
    QFileDialog, QColorDialog
)
from PySide6.QtGui import QPainter, QPen, QColor, QPolygonF
from PySide6.QtCore import Qt, QPointF, Signal

class DrawingCanvas(QGraphicsView):
    # Emits (area, perimeter) whenever you close a polygon.
    polyCompleted = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        # — Scene & view setup
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)

        # — Drawing pens
        self.pen       = QPen(Qt.black, 2)
        self.fill_pen  = QPen(Qt.blue, 2)
        self.fill_brush= QColor(0, 0, 255, 40)

        # — State
        self.tool           = None       # only 'wall' in this version
        self.current_points = []         # list[QPointF]
        self.preview_line   = None
        self.snap_dist      = 10

        # allow mouseMoveEvent() even when no button is down
        self.setMouseTracking(True)

    def set_tool(self, name):
        """Only 'wall' supported.  Any other tool turns it off."""
        self.tool = name
        if name != 'wall':
            self._clear_preview()

    def upload_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Upload Photo", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path:
            return
        pix = self.scene.addPixmap(QColor(path))  # <-- if you want real QPixmap: QPixmap(path)
        pix.setZValue(-1)

    def pick_color(self):
        col = QColorDialog.getColor(self.pen.color(), self, "Pick Line Color")
        if col.isValid():
            self.pen.setColor(col)

    def clear(self):
        """Remove all polygons & previews (keep any background pixmap)."""
        for item in list(self.scene.items()):
            if isinstance(item, QGraphicsPolygonItem) or item is self.preview_line:
                self.scene.removeItem(item)
        self._clear_preview()

    def mousePressEvent(self, ev):
        if self.tool == 'wall' and ev.button() == Qt.LeftButton:
            pos = self.mapToScene(ev.pos())

            # — snap to any existing polygon vertex
            for item in self.scene.items():
                if isinstance(item, QGraphicsPolygonItem):
                    for pt in item.polygon():
                        if (pt - pos).manhattanLength() < self.snap_dist:
                            pos = pt
                            break

            # — first click: start new poly
            if not self.current_points:
                self.current_points.append(pos)
            else:
                # if close to first point and ≥3 pts => finish
                if (pos - self.current_points[0]).manhattanLength() < self.snap_dist and len(self.current_points) >= 3:
                    self._finish_polygon()
                    return
                self.current_points.append(pos)

            self._update_preview(pos)
            return

        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self.tool == 'wall' and self.current_points:
            pos = self.mapToScene(ev.pos())
            self._update_preview(pos)
            return
        super().mouseMoveEvent(ev)

    def _update_preview(self, pos: QPointF):
        """Draw a temporary line from last fixed point → mouse."""
        if self.preview_line:
            self.scene.removeItem(self.preview_line)
        last = self.current_points[-1]
        self.preview_line = self.scene.addLine(
            last.x(), last.y(), pos.x(), pos.y(), self.pen
        )

    def _clear_preview(self):
        if self.preview_line:
            self.scene.removeItem(self.preview_line)
            self.preview_line = None
        self.current_points.clear()

    def _finish_polygon(self):
        """When user closes the loop: draw a filled QGraphicsPolygonItem,
           compute area/perimeter, emit signal."""
        poly = QPolygonF(self.current_points)
        item = QGraphicsPolygonItem(poly)
        item.setPen(self.fill_pen)
        item.setBrush(self.fill_brush)
        self.scene.addItem(item)

        # — shoelace formula for area
        area = abs(sum(
            poly[i].x()*poly[(i+1)%len(poly)].y()
           -poly[(i+1)%len(poly)].x()*poly[i].y()
            for i in range(len(poly))
        )/2)

        # — perimeter by sum of segment lengths
        perimeter = sum(
            (poly[i] - poly[(i+1)%len(poly)]).manhattanLength()
            for i in range(len(poly))
        )

        self.polyCompleted.emit(area, perimeter)
        self._clear_preview()
