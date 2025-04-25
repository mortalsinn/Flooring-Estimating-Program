diff --git a/drawing_canvas.py b/drawing_canvas.py
index abcdef0..1234567 100644
--- a/drawing_canvas.py
+++ b/drawing_canvas.py
@@ -1,6 +1,7 @@
-# drawing_canvas.py
+# drawing_canvas.py — v1.15.1
+
+from PySide6.QtWidgets import (
     QGraphicsView, QGraphicsScene, QFileDialog, QColorDialog
 )
 from PySide6.QtGui import (
@@ -10,7 +11,8 @@ from PySide6.QtCore import Qt, QRectF, QPointF
 from PySide6.QtWidgets import (
     QGraphicsLineItem, QGraphicsRectItem,
     QGraphicsPathItem, QGraphicsTextItem,
-    QGraphicsPixmapItem
+    QGraphicsPixmapItem,
+)
 
 
 class DrawingCanvas(QGraphicsView):
@@ -22,15 +24,17 @@ class DrawingCanvas(QGraphicsView):
         self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
         self.setMouseTracking(True)
 
-        # pens
+        # ─── Pens & State
         self.pen = QPen(Qt.black, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
         self.brush_pen = QPen(QColor('#FFEB3B'), 10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
         self.tool = None
         self.current_item = None
 
-        # ruler
+        # ─── Ruler Overlay
         self.show_ruler = False
-        self.ruler_items = []
+        self.ruler_items = []
 
-        # scale & units
+        # ─── Scale & Units
         self.scale = 1.0
         self.unit_type = 'px/unit'
 
 
@@ -58,7 +62,7 @@ class DrawingCanvas(QGraphicsView):
     def set_tool(self, name):
         """Activate one of: 'line', 'rect', 'brush', 'ruler' (or None)."""
-        self.current_item = None
+        self.current_item = None
 
         # Ruler toggling
         if name == 'ruler':
@@ -66,13 +70,24 @@ class DrawingCanvas(QGraphicsView):
         self.tool = name
 
     def clear(self):
-        for it in list(self._scene.items()):
-            if not isinstance(it, QGraphicsPixmapItem):
-                self._scene.removeItem(it)
-        if self.show_ruler:
-            self._draw_ruler()
+        """Remove all drawn items but keep background pixmap."""
+        for it in list(self._scene.items()):
+            if not isinstance(it, QGraphicsPixmapItem):
+                self._scene.removeItem(it)
+        if self.show_ruler:
+            self._draw_ruler()
 
     def upload_photo(self):
-        path, _ = QFileDialog.getOpenFileName(
+        """Launch file dialog, load and insert a background pixmap."""
+        path, _ = QFileDialog.getOpenFileName(
             self, "Upload Photo", "", "Images (*.png *.jpg *.jpeg *.bmp)"
         )
         if not path:
@@ -81,7 +96,16 @@ class DrawingCanvas(QGraphicsView):
         pix = QPixmap(path)
         pix = pix.scaled(vw, vh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
 
-        item = QGraphicsPixmapItem(pix)
+        # add behind everything
+        item = QGraphicsPixmapItem(pix)
         item.setZValue(-1)
         self._scene.addItem(item)
+    
+    def pick_color(self):
+        """Open color dialog to set brush color."""
+        col = QColorDialog.getColor(self.brush_pen.color(), self, "Pick Color")
+        if col.isValid():
+            self.brush_pen.setColor(col)
+
     def set_unit_type(self, u):
         self.unit_type = u
 
@@ -98,14 +122,49 @@ class DrawingCanvas(QGraphicsView):
 
     def _draw_ruler(self):
         """Overlay X/Y axes plus tick marks every 100px."""
-        self._clear_ruler()
+        self._clear_ruler()
         pen = QPen(Qt.black, 1)
         w, h = self.viewport().width(), self.viewport().height()
         self.ruler_items.append(self._scene.addLine(0, 0, w, 0, pen))
         self.ruler_items.append(self._scene.addLine(0, 0, 0, h, pen))
-        for x in range(0, w, 100):
-            self.ruler_items.append(self._scene.addLine(x, 0, x, 5, pen))
-        for y in range(0, h, 100):
-            self.ruler_items.append(self._scene.addLine(0, y, 5, y, pen))
+        for x in range(0, w, 100):
+            self.ruler_items.append(self._scene.addLine(x, 0, x, 5, pen))
+        for y in range(0, h, 100):
+            self.ruler_items.append(self._scene.addLine(0, y, 5, y, pen))
 
     def _clear_ruler(self):
-        for it in self.ruler_items:
-            self._scene.removeItem(it)
+        for it in self.ruler_items:
+            self._scene.removeItem(it)
         self.ruler_items.clear()
 
     def mousePressEvent(self, ev):
         if ev.button() == Qt.LeftButton and self.tool:
+            # anchor at the true click point
             pt = self.mapToScene(ev.pos())
             if self.tool == 'line':
                 ln = QGraphicsLineItem(pt.x(), pt.y(), pt.x(), pt.y())
@@ -117,7 +176,9 @@ class DrawingCanvas(QGraphicsView):
             if self.tool == 'brush':
                 path = QPainterPath(pt)
                 bp = QGraphicsPathItem(path)
-                bp.setPen(self.brush_pen); self.current_item = bp
+                bp.setPen(self.brush_pen)
+                self.current_item = bp
+                # now will start exactly at pt
                 self._scene.addItem(bp)
                 return
         super().mousePressEvent(ev)
@@ -164,7 +225,8 @@ class DrawingCanvas(QGraphicsView):
     def mouseReleaseEvent(self, ev):
         if ev.button() == Qt.LeftButton and self.current_item:
             if isinstance(self.current_item, (QGraphicsLineItem, QGraphicsRectItem)):
-                self._annotate(self.current_item)
+                self._annotate(self.current_item)
             self.current_item = None
             return
         super().mouseReleaseEvent(ev)
diff --git a/main.py b/main.py
index fedcba9..7654321 100644
--- a/main.py
+++ b/main.py
@@ -1,6 +1,6 @@
-# main.py — Flooring Estimator v1.15.0
+# main.py — Flooring Estimator v1.15.1
 
 import sys, os
