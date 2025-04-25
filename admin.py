import utils
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QDoubleSpinBox, QSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Signal

class AdminTab(QWidget):
    products_updated = Signal()

    def __init__(self, default, user):
        super().__init__()
        self.default = default
        self.user    = user

        L = QVBoxLayout(self)
        self.table = QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(
            ["Cat","Supplier","Series","Color","Price","SKU"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellClicked.connect(self._on_select)
        L.addWidget(self.table)

        form = QFormLayout()
        self.cat   = QLineEdit(); form.addRow("Category", self.cat)
        self.sup   = QLineEdit(); form.addRow("Supplier", self.sup)
        self.ser   = QLineEdit(); form.addRow("Series", self.ser)
        self.col   = QLineEdit(); form.addRow("Color", self.col)
        self.price = QDoubleSpinBox(); self.price.setPrefix("$"); form.addRow("Price", self.price)
        self.sku   = QLineEdit(); form.addRow("SKU", self.sku)
        L.addLayout(form)

        B = QHBoxLayout()
        self.add = QPushButton("Add");    self.add.clicked.connect(self._add)
        self.upd = QPushButton("Update"); self.upd.clicked.connect(self._update)
        self.del_ = QPushButton("Delete");self.del_.clicked.connect(self._delete)
        B.addWidget(self.add); B.addWidget(self.upd); B.addWidget(self.del_)
        L.addLayout(B)

        self._refresh()

    def _refresh(self):
        self.table.setRowCount(0)
        merged = utils.merge_products(self.default, self.user)
        for r,p in enumerate(merged):
            self.table.insertRow(r)
            for c,key in enumerate(['category','supplier','series','color']):
                self.table.setItem(r,c,QTableWidgetItem(p[key]))
            self.table.setItem(r,4,QTableWidgetItem(f"${p['price']:.2f}"))
            self.table.setItem(r,5,QTableWidgetItem(p['sku']))
        self.add.setEnabled(True)
        self.upd.setEnabled(self.del_.isEnabled()==False)
        self.del_.setEnabled(False)

    def _on_select(self,r,c):
        merged = utils.merge_products(self.default, self.user)
        p = merged[r]
        for w,key in [(self.cat,'category'),(self.sup,'supplier'),
                      (self.ser,'series'),(self.col,'color')]:
            w.setText(p[key])
        self.price.setValue(p['price'])
        self.sku.setText(p['sku'])
        self.add.setEnabled(False); self.upd.setEnabled(True); self.del_.setEnabled(True)

    def _add(self):
        p = {
          'category':self.cat.text(),
          'supplier':self.sup.text(),
          'series':  self.ser.text(),
          'color':   self.col.text(),
          'price':   self.price.value(),
          'sku':     self.sku.text()
        }
        self.user.append(p)
        utils.save_user_products(self.user)
        self.products_updated.emit()
        self._refresh()

    def _update(self):
        # remove any with same 4-key, then add new
        key = (self.cat.text(),self.sup.text(),self.ser.text(),self.col.text())
        self.user = [u for u in self.user
                     if (u['category'],u['supplier'],u['series'],u['color'])!=key]
        self._add()

    def _delete(self):
        key = (self.cat.text(),self.sup.text(),self.ser.text(),self.col.text())
        self.user = [u for u in self.user
                     if (u['category'],u['supplier'],u['series'],u['color'])!=key]
        utils.save_user_products(self.user)
        self.products_updated.emit()
        self._refresh()
