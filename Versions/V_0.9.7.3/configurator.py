import json
import os
import shutil
import sys
import re

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QSpinBox, QToolButton, QVBoxLayout, QWidget
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(APP_DIR, "config.json")
ASSETS_DIR = os.path.join(APP_DIR, "assets_icons")
ICONS_DIR = os.path.join(APP_DIR, "icons")

COLS, ROWS, MAX_PAGES = 5, 3, 10

def ensure_dirs():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(ICONS_DIR, exist_ok=True)

def empty_config():
    return {"pc_ip": "192.168.15.56", "current_page": 1, "pages": {}}

def load_config(path: str):
    if not os.path.exists(path): return empty_config()
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

def save_config(path: str, cfg: dict):
    with open(path, "w", encoding="utf-8") as f: json.dump(cfg, f, ensure_ascii=False, indent=2)

def get_slot(cfg: dict, page: int, btn_id: int):
    return cfg.get("pages", {}).get(f"p{page}", {}).get(f"b{btn_id}")

def set_slot(cfg: dict, page: int, btn_id: int, slot: dict | None):
    cfg.setdefault("pages", {}).setdefault(f"p{page}", {})
    if slot is None:
        cfg["pages"][f"p{page}"].pop(f"b{btn_id}", None)
    else:
        cfg["pages"][f"p{page}"][f"b{btn_id}"] = slot

def normalize_icon_dest_name(src_path: str) -> str:
    base = re.sub(r"[^a-z0-9_.-]", "_", os.path.basename(src_path).lower())
    return base

def import_icon(src_path: str) -> str:
    if not src_path: return ""
    ensure_dirs()
    name = normalize_icon_dest_name(src_path)
    dst_assets = os.path.join(ASSETS_DIR, name)
    dst_icons = os.path.join(ICONS_DIR, name)
    if os.path.abspath(src_path) != os.path.abspath(dst_assets): shutil.copy2(src_path, dst_assets)
    if os.path.abspath(src_path) != os.path.abspath(dst_icons): shutil.copy2(src_path, dst_icons)
    return f"icons/{name}"

def icon_abs_from_rel(icon_rel: str) -> str:
    if not icon_rel: return ""
    icon_rel = icon_rel.replace("\\", "/")
    if icon_rel.startswith(("icons/", "assets_icons/")): return os.path.join(APP_DIR, icon_rel.replace("/", os.sep))
    p1 = os.path.join(ICONS_DIR, icon_rel.replace("/", os.sep))
    return p1 if os.path.exists(p1) else os.path.join(ASSETS_DIR, icon_rel.replace("/", os.sep))

def iter_used_icons(cfg: dict):
    for page_obj in cfg.get("pages", {}).values():
        if isinstance(page_obj, dict):
            for slot in page_obj.values():
                if isinstance(slot, dict) and slot.get("icon"): yield slot["icon"]

class TileButton(QToolButton):
    def __init__(self, btn_id: int, parent=None):
        super().__init__(parent)
        self.btn_id = btn_id
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setFixedSize(200, 150)
        self.setIconSize(QSize(180, 130))
        self.setStyleSheet("QToolButton { background-color: #0f1219; border: 2px solid #283246; border-radius: 6px; } QToolButton:hover { border: 2px solid #4a6fb0; } QToolButton:checked { border: 3px solid #6aa6ff; }")
        self.setCheckable(True)
    def mouseDoubleClickEvent(self, ev):
        if hasattr(self.window(), "open_editor"): self.window().open_editor(self)

class EditSlotDialog(QDialog):
    def __init__(self, page: int, btn_id: int, slot: dict | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Configurar: Page {page}, Key {btn_id}")
        self.resize(520, 260)
        self.result_slot = None

        self.type_combo = QComboBox()
        self.type_combo.addItems(["open_app", "open_url", "hotkey", "goto_page", "empty"])
        self.app_path, self.url, self.hotkey, self.icon_path = QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit()
        self.hotkey.setPlaceholderText("Ex: CTRL+SHIFT+S")
        self.goto_page = QSpinBox()
        self.goto_page.setRange(1, MAX_PAGES)
        self.btn_pick_app, self.btn_pick_icon = QPushButton("Select App…"), QPushButton("Select Icon…")
        self.btn_pick_app.clicked.connect(self.pick_app)
        self.btn_pick_icon.clicked.connect(self.pick_icon)

        form = QGridLayout()
        form.addWidget(QLabel("Type:"), 0, 0); form.addWidget(self.type_combo, 0, 1, 1, 3)
        form.addWidget(QLabel("Open App:"), 1, 0); form.addWidget(self.app_path, 1, 1, 1, 2); form.addWidget(self.btn_pick_app, 1, 3)
        form.addWidget(QLabel("Open URL:"), 2, 0); form.addWidget(self.url, 2, 1, 1, 3)
        form.addWidget(QLabel("Hotkey:"), 3, 0); form.addWidget(self.hotkey, 3, 1, 1, 3)
        form.addWidget(QLabel("Goto Page:"), 4, 0); form.addWidget(self.goto_page, 4, 1, 1, 3)
        form.addWidget(QLabel("Icon file:"), 5, 0); form.addWidget(self.icon_path, 5, 1, 1, 2); form.addWidget(self.btn_pick_icon, 5, 3)

        box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel | QDialogButtonBox.Reset)
        box.accepted.connect(self.on_save); box.rejected.connect(self.reject); box.button(QDialogButtonBox.Reset).clicked.connect(self.on_clear)
        root = QVBoxLayout(self); root.addLayout(form); root.addStretch(1); root.addWidget(box)

        if slot:
            self.type_combo.setCurrentText(slot.get("type", "open_app"))
            self.app_path.setText(slot.get("path", ""))
            self.url.setText(slot.get("url", ""))
            self.hotkey.setText("+".join(slot.get("keys", [])) if isinstance(slot.get("keys"), list) else "")
            self.goto_page.setValue(int(slot.get("page", 1)))
            self.icon_path.setText(slot.get("icon", ""))
        self.type_combo.currentTextChanged.connect(self.update_enabled); self.update_enabled()

    def update_enabled(self):
        t = self.type_combo.currentText()
        self.app_path.setEnabled(t == "open_app"); self.btn_pick_app.setEnabled(t == "open_app")
        self.url.setEnabled(t == "open_url"); self.hotkey.setEnabled(t == "hotkey")
        self.goto_page.setEnabled(t == "goto_page"); self.icon_path.setEnabled(t != "empty"); self.btn_pick_icon.setEnabled(t != "empty")

    def pick_app(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select application", "", "Executables (*.exe);;All files (*.*)")
        if path: self.app_path.setText(path)
    def pick_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select icon (PNG/JPG)", "", "Images (*.png *.jpg *.jpeg);;All files (*.*)")
        if path: self.icon_path.setText(path)
    def on_clear(self):
        self.type_combo.setCurrentText("empty"); self.app_path.clear(); self.url.clear(); self.hotkey.clear(); self.icon_path.clear(); self.goto_page.setValue(1)

    def on_save(self):
        t = self.type_combo.currentText()
        if t == "empty": self.result_slot = None; self.accept(); return
        icon_rel = import_icon(self.icon_path.text().strip()) if os.path.isabs(self.icon_path.text().strip()) else self.icon_path.text().strip().replace("\\", "/")
        if t == "open_app": self.result_slot = {"type": "open_app", "path": self.app_path.text().strip(), "icon": icon_rel}
        elif t == "open_url": self.result_slot = {"type": "open_url", "url": self.url.text().strip(), "icon": icon_rel}
        elif t == "hotkey": self.result_slot = {"type": "hotkey", "keys": [k.strip().upper() for k in self.hotkey.text().strip().split("+") if k.strip()], "icon": icon_rel}
        elif t == "goto_page": self.result_slot = {"type": "goto_page", "page": int(self.goto_page.value()), "icon": icon_rel}
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_dirs()
        self.setWindowTitle("Switch Deck Configurator")
        self.cfg_path = DEFAULT_CONFIG_PATH
        self.cfg = load_config(self.cfg_path)

        central = QWidget(); self.setCentralWidget(central); root = QVBoxLayout(central)
        top = QHBoxLayout(); top.addWidget(QLabel("Page:"))
        self.page_buttons = []
        for p in range(1, MAX_PAGES + 1):
            b = QPushButton(str(p)); b.setCheckable(True); b.clicked.connect(lambda checked, pp=p: self.set_page(pp))
            self.page_buttons.append(b); top.addWidget(b)
            
        top.addStretch(1)
        top.addWidget(QLabel("PC IP:")); self.ip_input = QLineEdit(); self.ip_input.setText(self.cfg.get("pc_ip", "192.168.15.56")); self.ip_input.setFixedWidth(120); top.addWidget(self.ip_input)
        self.btn_send = QPushButton("SAVE TO SWITCH"); self.btn_send.setStyleSheet("font-weight: bold; background-color: #2e7d32; color: white; padding: 6px 16px;"); self.btn_send.clicked.connect(self.send_to_switch); top.addWidget(self.btn_send)
        root.addLayout(top)

        grid_box = QGroupBox(); grid = QGridLayout(grid_box); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(12)
        self.tiles = []
        for r in range(ROWS):
            for c in range(COLS):
                tb = TileButton(r * COLS + c + 1); tb.clicked.connect(lambda checked, b=tb: self.on_tile_clicked(b))
                self.tiles.append(tb); grid.addWidget(tb, r, c)

        root.addWidget(grid_box)
        self.current_page = int(self.cfg.get("current_page", 1))
        self.refresh_ui()

    def set_page(self, page: int): self.current_page = page; self.cfg["current_page"] = page; self.refresh_ui()
    def on_tile_clicked(self, tb: TileButton):
        for t in self.tiles: t.setChecked(t is tb)
    def open_editor(self, tb: TileButton):
        dlg = EditSlotDialog(self.current_page, tb.btn_id, get_slot(self.cfg, self.current_page, tb.btn_id), self)
        if dlg.exec() == QDialog.Accepted: set_slot(self.cfg, self.current_page, tb.btn_id, dlg.result_slot); self.refresh_ui()

    def refresh_ui(self):
        for i, b in enumerate(self.page_buttons, start=1): b.setChecked(i == self.current_page)
        for tb in self.tiles:
            slot = get_slot(self.cfg, self.current_page, tb.btn_id)
            icon_abs = icon_abs_from_rel(slot["icon"]) if slot and slot.get("icon") else ""
            tb.setIcon(QIcon(icon_abs) if icon_abs and os.path.exists(icon_abs) else QIcon())

    def send_to_switch(self):
        self.cfg["pc_ip"] = self.ip_input.text().strip()
        save_config(self.cfg_path, self.cfg)
        folder = QFileDialog.getExistingDirectory(self, "Selecione a pasta destino no Cartão SD (ex: SD:/switch/streamdeck_proto)")
        if not folder: return
        save_config(os.path.join(folder, "config.json"), self.cfg)
        dst_icons = os.path.join(folder, "icons"); os.makedirs(dst_icons, exist_ok=True)
        copied = 0
        for icon_rel in iter_used_icons(self.cfg):
            if icon_rel.replace("\\", "/").startswith("icons/"):
                src_abs = os.path.join(APP_DIR, icon_rel.replace("/", os.sep))
                if os.path.exists(src_abs): shutil.copy2(src_abs, os.path.join(dst_icons, os.path.basename(src_abs))); copied += 1
        QMessageBox.information(self, "Sucesso", f"Enviado para a pasta!\nLembrete: O IP gravado foi {self.cfg['pc_ip']}")

if __name__ == "__main__":
    app = QApplication(sys.argv); w = MainWindow(); w.show(); sys.exit(app.exec())