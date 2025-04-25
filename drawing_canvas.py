# drawing_canvas.py — v1.2 (extended for line+curve)

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QFileDialog, QColorDialog
from PySide6.QtGui     import QPainter, QPen, QColor, QPainterPath
from PySide6.QtCore    import Qt, QRectF, QPointF
from PySide6.QtWidgets import (
    QGraphicsLineItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsPixmapItem
)

class DrawingCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setMouseTracking(True)

        # pens & state
        self.pen         = QPen(Qt.black, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.brush_pen   = QPen(QColor('#FFEB3B'), 10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.tool        = None
        self.current_item= None
        self.unit_type   = 'px/unit'
        self.scale       = 1.0

    def set_tool(self, name):
        self.tool = name

    def set_unit_type(self, u):
        self.unit_type = u

    def set_scale(self, s):
        self.scale = s

    def clear(self):
        for it in list(self.scene.items()):
            if not isinstance(it, QGraphicsPixmapItem):
                self.scene.removeItem(it)

    def upload_photo(self):
        path,_ = QFileDialog.getOpenFileName(self,"Upload Photo","","Images (*.png *.jpg *.jpeg *.bmp)")
        if not path: return
        pix = QGraphicsPixmapItem(QPixmap(path))
        pix.setZValue(-1)
        self.scene.addItem(pix)

    def pick_color(self):
        col = QColorDialog.getColor(self.brush_pen.color(), self, "Pick Color")
        if col.isValid():
            self.brush_pen.setColor(col)

    def mousePressEvent(self, ev):
        pt = self.mapToScene(ev.pos())
        if ev.button()==Qt.LeftButton and self.tool in ('line','curve'):
            if self.tool=='line':
                ln = QGraphicsLineItem(pt.x(),pt.y(),pt.x(),pt.y())
                ln.setPen(self.pen); self.current_item = ln; self.scene.addItem(ln)
            else:  # curve
                path = QPainterPath(pt)
                cp   = QGraphicsPathItem(path)
                cp.setPen(self.pen); self.current_item = cp; self.scene.addItem(cp)
            return
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        pt = self.mapToScene(ev.pos())
        if ev.buttons() & Qt.LeftButton and self.current_item:
            if isinstance(self.current_item, QGraphicsLineItem):
                line = self.current_item.line(); line.setP2(pt); self.current_item.setLine(line)
            elif isinstance(self.current_item, QGraphicsPathItem):
                p = self.current_item.path(); p.lineTo(pt); self.current_item.setPath(p)
            return
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        if ev.button()==Qt.LeftButton and self.current_item:
            self._annotate(self.current_item)
            self.current_item = None
            return
        super().mouseReleaseEvent(ev)

    def _annotate(self, item):
        if isinstance(item, QGraphicsLineItem):
            p1,p2 = item.line().p1(), item.line().p2()
            dist = ((p2.x()-p1.x())**2 + (p2.y()-p1.y())**2)**0.5 / self.scale
            txt  = f"{dist:.1f} {self.unit_type}"
            mid  = QPointF((p1.x()+p2.x())/2,(p1.y()+p2.y())/2)
            ti   = QGraphicsTextItem(txt); ti.setDefaultTextColor(Qt.black); ti.setPos(mid)
            self.scene.addItem(ti)
        # curves aren’t auto‐annotated, but you could add length/area here
