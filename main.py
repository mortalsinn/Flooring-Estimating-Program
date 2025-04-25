# main.py — Flooring Estimator v1.15.1
# main.py — Flooring Estimator v1.15.1
"""
FEATURE CHECKLIST
────────────────────────
[Estimate Tab]
  • Browse by Category → Product → Area → +Add – calculates Subtotal, GST, Total
  • “Customer Copy” preview & print

[Admin Tab]
  • View default + custom products
  • Add / Update / Delete (password-protected)

[Room Designer]
  • Upload Photo background
  • Draw Line  → real-time measurement annotation
  • Draw Rectangle → width/height annotation
  • Draw Brush → freehand sketch starting exactly at click
  • Ruler Overlay → non-destructive, toggle on/off
  • Clear Canvas → removes all drawing but leaves photo

All other tabs/functions remain untouched.
"""
import sys, os

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QHBoxLayout,
    QPushButton, QWidget, QVBoxLayout, QSplitter, QLabel,
    QToolBar, QComboBox, QDoubleSpinBox
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QInputDialog, QMessageBox, QFrame,
    QDialog, QTextEdit, QAbstractItemView
)
from PySide6.QtGui import QAction, QActionGroup, QPixmap, QFont, QPalette, QColor
from PySide6.QtCore import Qt

import database
import utils
from drawing_canvas import DrawingCanvas

VERSION = "1.15.1"


class StyledApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setStyle('Fusion')
        p = QPalette()
        p.setColor(QPalette.Window, QColor('#E3F2FD'))
        p.setColor(QPalette.Base, QColor('#FFFFFF'))
        p.setColor(QPalette.Text, QColor('#333333'))
        p.setColor(QPalette.Button, QColor('#2196F3'))
        p.setColor(QPalette.ButtonText, QColor('#FFFFFF'))
        p.setColor(QPalette.Highlight, QColor('#64B5F6'))
        p.setColor(QPalette.HighlightedText, QColor('#000000'))
        self.setPalette(p)
        self.setFont(QFont('Segoe UI', 10))


# ───────────────── Estimate Tab ─────────────────────────────────────────────
class EstimateTab(QWidget):
    def __init__(self, products):
        super().__init__()
        self.products_list = products
        self.items = []
        self._build_ui()
        self._wire()
        self._load_products()
        self._refresh()

    def _build_ui(self):
        L = QVBoxLayout(self)
        row = QHBoxLayout()
        self.cat  = QComboBox(); row.addWidget(QLabel("Category:")); row.addWidget(self.cat)
        self.prod = QComboBox(); row.addWidget(QLabel("Product:"));  row.addWidget(self.prod)
        self.area = QDoubleSpinBox(); self.area.setSuffix(" sq ft"); self.area.setRange(0,1e6)
        row.addWidget(QLabel("Area:")); row.addWidget(self.area)
        self.add  = QPushButton("+ Add Item"); row.addWidget(self.add)
        L.addLayout(row)

        self.table = QTableWidget(0,4)
        self.table.setHorizontalHeaderLabels(["Product","Unit $","Qty","Line $"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        L.addWidget(self.table)

        bot = QHBoxLayout()
        self.sub   = QLabel("Subtotal: $0.00"); bot.addWidget(self.sub)
        self.gst   = QLabel("GST (5%): $0.00"); bot.addWidget(self.gst)
        self.total = QLabel("<b>Total: $0.00</b>"); bot.addWidget(self.total)
        bot.addStretch()
        self.preview = QPushButton("Customer Copy"); bot.addWidget(self.preview)
        L.addLayout(bot)

    def _wire(self):
        self.cat.currentIndexChanged.connect(self._on_cat)
        self.add.clicked.connect(self._add)
        self.preview.clicked.connect(lambda: CustomerCopy(self, self.items).exec())

    def _load_products(self):
        cats = sorted({p['category'] for p in self.products_list})
        self.cat.addItems(cats)
        self._on_cat(0)

    def _on_cat(self, _):
        cat = self.cat.currentText()
        self.prod.clear()
        subset = [p for p in self.products_list if p['category']==cat]
        for p in sorted(subset, key=lambda x: x['name']):
            self.prod.addItem(f"{p['name']} (${p['price']:.2f})", p)

    def _add(self):
        p, q = self.prod.currentData(), self.area.value()
        if not p or q<=0: return
        self.items.append({'prod':p,'qty':q})
        self.area.setValue(0)
        self._refresh()

    def _refresh(self):
        self.table.setRowCount(len(self.items))
        subtotal = 0.0
        for i,it in enumerate(self.items):
            p, q = it['prod'], it['qty']
            u, lt = p['price'], p['price']*q
            subtotal += lt
            for col, txt in enumerate((p['name'], f"${u:.2f}", f"{q:.2f}", f"${lt:.2f}")):
                self.table.setItem(i, col, QTableWidgetItem(txt))
        gst = subtotal * 0.05
        self.sub.setText(f"Subtotal: ${subtotal:.2f}")
        self.gst.setText(f"GST (5%): ${gst:.2f}")
        self.total.setText(f"<b>Total: ${(subtotal+gst):.2f}</b>")


class CustomerCopy(QDialog):
    def __init__(self, parent, lines):
        super().__init__(parent)
        self.setWindowTitle("Customer Estimate")
        self.resize(600,500)
        L = QVBoxLayout(self)

        hb = QHBoxLayout()
        logo = QLabel()
        lp = os.path.join(os.path.dirname(__file__),'assets','logo.png')
        if os.path.exists(lp):
            logo.setPixmap(
                QPixmap(lp)
                .scaled(80,80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        hb.addWidget(logo)
        hb.addWidget(QLabel("<h2>Estimate</h2>"))
        hb.addStretch()
        L.addLayout(hb)
        L.addWidget(self._sep())

        tbl = QTableWidget(len(lines),4)
        tbl.setHorizontalHeaderLabels(["Item","Qty","Unit","Line Total"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        total = 0
        for r,l in enumerate(lines):
            p, q = l['prod'], l['qty']
            u, lt = p['price'], p['price']*q
            total += lt
            for c,v in enumerate((p['name'], f"{q:.2f}", f"${u:.2f}", f"${lt:.2f}")):
                tbl.setItem(r, c, QTableWidgetItem(v))
        L.addWidget(tbl)
        L.addWidget(self._sep())

        gst = total * 0.05
        ft = QTextEdit(); ft.setReadOnly(True)
        ft.setHtml(
            f"<b>Subtotal:</b> ${total:.2f}<br>"
            f"<b>GST (5%):</b> ${gst:.2f}<br>"
            f"<h2>Total:</h2> <h3>${(total+gst):.2f}</h3>"
        )
        L.addWidget(ft)
        btn = QPushButton("Print")
        from PySide6.QtPrintSupport import QPrinter, QPrintDialog
        btn.clicked.connect(lambda: QPrintDialog(QPrinter(), self).print_())
        L.addWidget(btn, alignment=Qt.AlignRight)

    def _sep(self):
        f = QFrame(); f.setFrameShape(QFrame.HLine); f.setFrameShadow(QFrame.Sunken)
        return f


# ───────────────── Admin Tab ────────────────────────────────────────────────
class AdminTab(QWidget):
    def __init__(self, default, user):
        super().__init__()
        self.default = default
        self.user    = user
        self._build_ui()
        self._wire()
        self._refresh_table()

    def _build_ui(self):
        L = QVBoxLayout(self)
        self.table = QTableWidget(0,5)
        self.table.setHorizontalHeaderLabels(["Category","Brand","Name","Price","Margin%"])
        # fix: use QAbstractItemView.NoEditTriggers
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        L.addWidget(self.table)

        for label, widget in [
            ("Category:", QLineEdit()),
            ("Brand:",    QLineEdit()),
            ("Name:",     QLineEdit()),
            ("Price:",    QDoubleSpinBox()),
            ("Margin:",   QDoubleSpinBox()),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            if isinstance(widget, QDoubleSpinBox):
                widget.setRange(0,1e6)
                widget.setPrefix("$" if label=="Price:" else "")
                widget.setSuffix("" if label=="Price:" else " %")
            setattr(self, label[:-1].lower().replace(" ","_") + "_in", widget)
            row.addWidget(widget)
            L.addLayout(row)

        btns = QHBoxLayout()
        self.new  = QPushButton("New");    btns.addWidget(self.new)
        self.add  = QPushButton("Add");    btns.addWidget(self.add)
        self.upd  = QPushButton("Update"); btns.addWidget(self.upd)
        self.del_ = QPushButton("Delete"); btns.addWidget(self.del_)
        L.addLayout(btns)

    def _wire(self):
        self.table.cellClicked.connect(self._on_sel)
        self.new.clicked.connect(self._clear)
        self.add.clicked.connect(self._add)
        self.upd.clicked.connect(self._update)
        self.del_.clicked.connect(self._delete)

    def _refresh_table(self):
        combined = []
        ukeys = {(p['category'],p['brand'],p['name']) for p in self.user}
        for p in self.default:
            if (p['category'],p['brand'],p['name']) not in ukeys:
                combined.append((p,'default'))
        for p in self.user:
            combined.append((p,'user'))
        self.combined = combined
        self.table.setRowCount(len(combined))
        for i,(p,src) in enumerate(combined):
            vals = [
                p['category'], p['brand'], p['name'],
                f"${p['price']:.2f}", f"{p.get('margin',0):.0f}%"
            ]
            for j,v in enumerate(vals):
                self.table.setItem(i, j, QTableWidgetItem(v))
        self._clear()

    def _on_sel(self, r, _):
        p,src = self.combined[r]
        self.sel = r
        self.category_in.setText(p['category'])
        self.brand_in   .setText(p['brand'])
        self.name_in    .setText(p['name'])
        self.price_in   .setValue(p['price'])
        self.margin_in  .setValue(p.get('margin',0))
        self.add .setEnabled(False)
        self.upd .setEnabled(True)
        self.del_.setEnabled(True)

    def _clear(self):
        self.sel = None
        for fld in ('category','brand','name'):
            getattr(self, fld+"_in").clear()
        self.price_in .setValue(0)
        self.margin_in.setValue(0)
        self.add .setEnabled(True)
        self.upd .setEnabled(False)
        self.del_.setEnabled(False)
        self.table.clearSelection()

    def _add(self):
        cat = self.category_in.text().strip()
        br  = self.brand_in.  text().strip()
        nm  = self.name_in.   text().strip()
        pr  = self.price_in.  value()
        mg  = self.margin_in. value()
        if not(cat and br and nm and pr>0):
            QMessageBox.warning(self,"Error","All fields & Price>0 required")
            return
        for p in self.default + self.user:
            if (p['category'],p['brand'],p['name']) == (cat,br,nm):
                QMessageBox.warning(self,"Error","Duplicate"); return
        new = {"category":cat,"brand":br,"name":nm,"price":pr,"margin":mg}
        self.user.append(new)
        utils.save_user_products(self.user)
        self._refresh_table()

    def _update(self):
        if self.sel is None: return
        p,src = self.combined[self.sel]
        if src=='default':
            self.default = [x for x in self.default
                            if (x['category'],x['brand'],x['name']) != (p['category'],p['brand'],p['name'])]
        else:
            self.user    = [x for x in self.user
                            if (x['category'],x['brand'],x['name']) != (p['category'],p['brand'],p['name'])]
        upd = {
            "category": self.category_in.text().strip(),
            "brand":    self.brand_in.  text().strip(),
            "name":     self.name_in.   text().strip(),
            "price":    self.price_in.  value(),
            "margin":   self.margin_in. value()
        }
        self.user.append(upd)
        utils.save_user_products(self.user)
        self._refresh_table()

    def _delete(self):
        if self.sel is None: return
        p,src = self.combined[self.sel]
        if src=='default':
            self.default = [x for x in self.default
                            if (x['category'],x['brand'],x['name']) != (p['category'],p['brand'],p['name'])]
        else:
            self.user = [x for x in self.user
                         if (x['category'],x['brand'],x['name']) != (p['category'],p['brand'],p['name'])]
            utils.save_user_products(self.user)
        self._refresh_table()


# ───────────────── Main Window ───────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Flooring Estimator v{VERSION}")
        self.resize(1000,700)

        default = database.PRODUCTS
        user    = utils.load_user_products()

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        self.est   = EstimateTab(default)
        self.room  = self._room_designer_tab()
        self.admin = AdminTab(default,user)

        tabs.addTab(self.est,   "Estimate")
        tabs.addTab(self.room,  "Room Designer")
        tabs.addTab(self.admin, "Admin")
        tabs.currentChanged.connect(self._on_tab)

# inside main.py — in MainWindow:

    def _room_designer_tab(self):
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
            QLabel, QToolBar, QAction, QComboBox, QDoubleSpinBox
        )

        w = QWidget()
        L = QVBoxLayout(w)

        # — toolbar
        tb     = QToolBar()
        upload = QAction("Upload Photo…", self)
        wall   = QAction("Walls",        self); wall.setCheckable(True)
        clear  = QAction("Clear",        self)
        pick   = QAction("Pick Color",   self)
        tb.addAction(upload)
        tb.addAction(wall)
        tb.addAction(clear)
        tb.addAction(pick)
        L.addWidget(tb)

        # — canvas + stats side by side
        from drawing_canvas import DrawingCanvas
        canvas = DrawingCanvas()
        stats_w = QWidget()
        stats_l = QVBoxLayout(stats_w)
        area_lbl      = QLabel("Area: 0")
        perimeter_lbl = QLabel("Perimeter: 0")
        stats_l.addWidget(area_lbl)
        stats_l.addWidget(perimeter_lbl)
        stats_l.addStretch()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(canvas)
        splitter.addWidget(stats_w)
        splitter.setStretchFactor(0,3)
        splitter.setStretchFactor(1,1)
        L.addWidget(splitter)

        # — hook up actions
        upload.triggered.connect(canvas.upload_photo)
        clear .triggered.connect(canvas.clear)
        pick  .triggered.connect(canvas.pick_color)
        wall  .toggled.connect(lambda on: canvas.set_tool('wall' if on else None))

        # — update stats when a polygon completes
        canvas.polyCompleted.connect(
            lambda a,p: (
                area_lbl.setText(f"Area: {a:.1f}"),
                perimeter_lbl.setText(f"Perimeter: {p:.1f}")
            )
        )

        return w

    def _on_tab(self, idx):
        if self.centralWidget().tabText(idx) == "Admin":
            u,ok = QInputDialog.getText(self,"Admin Login","Username:")
            if not(ok and u=="admin"):
                self.centralWidget().setCurrentIndex(0); return
            p,ok = QInputDialog.getText(self,"Admin Login","Password:",QLineEdit.Password)
            if not(ok and p=="flooring"):
                QMessageBox.warning(self,"Admin","Invalid credentials")
                self.centralWidget().setCurrentIndex(0)


if __name__=='__main__':
    app = StyledApp(sys.argv)
    w   = MainWindow()
    w.show()
    sys.exit(app.exec())
