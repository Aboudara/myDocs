# main_pyside.py

import sys
import serial.tools.list_ports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QCheckBox, QDialog, QGridLayout
)
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import QTimer

from comms import (
    ouvrir_connexion, construire_trame_ouverture, construire_trame_ouverture_permanente,
    envoyer_trame, lire_infos_entrees_sorties, trame_blocage_entree, trame_reinitialisation
)
from config import ADRESSES_PORTIQUES, PORT_COM_DEFAUT, PORTIQUES_INVERSES

ser = None
voyants_portiques = {}
etat_blocage = {adr: None for adr in ADRESSES_PORTIQUES}

class PasswordDialog(QDialog):
    def __init__(self, prompt, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mot de passe")
        self.result = None

        layout = QVBoxLayout()
        label = QLabel(prompt)
        self.entry = QLineEdit()
        self.entry.setEchoMode(QLineEdit.Password)
        bouton_ok = QPushButton("OK")
        bouton_ok.clicked.connect(self.on_ok)

        layout.addWidget(label)
        layout.addWidget(self.entry)
        layout.addWidget(bouton_ok)
        self.setLayout(layout)

    def on_ok(self):
        self.result = self.entry.text()
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Contrôle d'accès FB-MecSystem")
        self.showFullScreen()

        font_large = QFont("Segoe UI", 20)
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # ==== TOP: Logo et Titre ====
        logo = QLabel()
        pixmap = QPixmap("FBMecaSystem/FBMecaSystem1.png")
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaledToWidth(300))
        main_layout.addWidget(logo)

        title = QLabel("FB Counter - Site : La Cité")
        title.setFont(QFont("Segoe UI", 34, QFont.Bold))
        main_layout.addWidget(title)

        # ==== PORT COM & Connexion ====
        port_layout = QHBoxLayout()
        port_label = QLabel("Port COM:")
        self.entry_port = QLineEdit(PORT_COM_DEFAUT)
        self.btn_connect = QPushButton("Se connecter")
        self.btn_connect.setFont(font_large)
        self.btn_connect.clicked.connect(self.connecter_deconnecter)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.entry_port)
        port_layout.addWidget(self.btn_connect)
        main_layout.addLayout(port_layout)

        # ==== SEUIL ====
        seuil_layout = QHBoxLayout()
        seuil_label = QLabel("Seuil global:")
        self.entry_seuil = QLineEdit("1293")
        self.entry_seuil.setReadOnly(True)
        seuil_layout.addWidget(seuil_label)
        seuil_layout.addWidget(self.entry_seuil)
        main_layout.addLayout(seuil_layout)

        # ==== Portiques ====
        self.checkboxes = {}
        grid = QGridLayout()
        for i, adr in enumerate(ADRESSES_PORTIQUES):
            checkbox = QCheckBox(f"Portique {i + 1}")
            btn_entree = QPushButton("Entrée")
            btn_sortie = QPushButton("Sortie")
            voyant = QLabel("⬤")
            voyant.setStyleSheet("color: gray; font-size: 24px;")
            self.checkboxes[adr] = checkbox
            btn_entree.clicked.connect(lambda _, a=adr: self.envoyer(a, "entree"))
            btn_sortie.clicked.connect(lambda _, a=adr: self.envoyer(a, "sortie"))

            grid.addWidget(checkbox, i, 0)
            grid.addWidget(btn_entree, i, 1)
            grid.addWidget(btn_sortie, i, 2)
            grid.addWidget(voyant, i, 3)
            voyants_portiques[adr] = voyant

        main_layout.addLayout(grid)

        # ==== Modes Globaux ====
        global_modes = QHBoxLayout()
        btn_mode1 = QPushButton("🔒 Entrée/Sortie Bloquée")
        btn_mode2 = QPushButton("🔓 Entrée/Sortie Libre")
        btn_mode3 = QPushButton("🚪 Entrée Bloquée / Sortie Libre")
        global_modes.addWidget(btn_mode1)
        global_modes.addWidget(btn_mode2)
        global_modes.addWidget(btn_mode3)
        btn_mode1.clicked.connect(lambda: self.envoyer_mode_global(0x01))
        btn_mode2.clicked.connect(lambda: self.envoyer_mode_global(0x02))
        btn_mode3.clicked.connect(lambda: self.envoyer_mode_global(0x04))
        main_layout.addLayout(global_modes)

        # ==== RS485 Alerte ====
        self.label_alerte = QLabel("")
        main_layout.addWidget(self.label_alerte)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # ==== Timer update ====
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all)

    def verifier_mot_de_passe(self, password_required):
        dialog = PasswordDialog("Entrez le mot de passe :", self)
        if dialog.exec() == QDialog.Accepted:
            if dialog.result == password_required:
                return True
            else:
                QMessageBox.critical(self, "Erreur", "Mot de passe incorrect.")
        return False

    def connecter_deconnecter(self):
        global ser
        port = self.entry_port.text()
        if ser and ser.is_open:
            if not self.verifier_mot_de_passe("admin123"):
                return
            ser.close()
            ser = None
            self.btn_connect.setText("Se connecter")
            self.timer.stop()
        else:
            try:
                ser = ouvrir_connexion(port)
                self.btn_connect.setText("Se déconnecter")
                self.timer.start(2000)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def envoyer(self, adresse, sens):
        global ser
        port = self.entry_port.text()
        if PORTIQUES_INVERSES.get(adresse, False):
            sens = "sortie" if sens == "entree" else "entree"
        try:
            if ser and ser.is_open:
                trame = construire_trame_ouverture(adresse, sens)
                envoyer_trame(ser, trame)
            else:
                with ouvrir_connexion(port) as temp_ser:
                    trame = construire_trame_ouverture(adresse, sens)
                    envoyer_trame(temp_ser, trame)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def envoyer_mode_global(self, mode):
        QMessageBox.information(self, "Info", f"Mode global envoyé : {mode:02X}")

    def update_all(self):
        # Ici tu recopieras toute la logique de ton update_all Tkinter
        self.label_alerte.setText("Update... (à compléter)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
