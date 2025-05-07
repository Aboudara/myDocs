# main.py

#from interface import lancer_interface

#if __name__ == "__main__":
 #   lancer_interface()
import serial
import time
import tkinter as tk
from tkinter import ttk, messagebox


def calcul_checksum(trame):
    return sum(trame[1:15]) & 0xFF

def construire_trame_ouverture(adresse_portique, sens):
    trame = [0xAA, 0x00, 0x01, 0x02, 0x00, adresse_portique, 0x08]
    if sens == "entree":
        data = [0x00, 0x00, 0x00] + [0x00] * 5
    else:
        data = [0x00, 0x03, 0x00] + [0x00] * 5
    trame += data
    trame.append(calcul_checksum(trame))
    return bytes(trame)

def construire_trame_lecture(adresse_portique):
    trame = [0xAA, 0x00, 0x01, 0x02, 0x00, adresse_portique, 0x08, 0xFF]
    trame += [0x00] * 7
    trame.append(calcul_checksum(trame))
    return bytes(trame)

def envoyer_trame(port_com, trame):
    try:
        with serial.Serial(port_com, baudrate=9600, bytesize=8, stopbits=1, parity='N', timeout=1) as ser:
            ser.write(trame)
            print("✅ Trame envoyée :", ' '.join(f'{b:02X}' for b in trame))
    except Exception as e:
        print("❌ Erreur d'envoi:", e)
        messagebox.showerror("Erreur", str(e))

def lire_infos_entrees_sorties(port_com, adresse_portique):
    trame = construire_trame_lecture(adresse_portique)
    try:
        with serial.Serial(port_com, baudrate=9600, bytesize=8, stopbits=1, parity='N', timeout=1) as ser:
            ser.write(trame)
            time.sleep(0.5)
            response = ser.read(16)
            print("🔎 Réponse brute:", ' '.join(f'{b:02X}' for b in response))

            if len(response) == 16 and response[0] == 0xAA:
                entree = (response[11]) | (response[10] << 8) | (response[9] << 16)
                sortie = (response[14]) | (response[13] << 8) | (response[12] << 16)
                return entree, sortie
            else:
                print("❌ Réponse invalide.")
                return None, None
    except Exception as e:
        print("❌ Erreur communication:", e)
        return None, None

def trame_blocage_entree(adresse_portique, mode):
    # mode = 0x04 pour bloquer, 0x02 pour débloquer
    trame = [
        0xAA, 0x00, 0x01, 0x02, 0x06, adresse_portique, 0x08,
        mode, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ]
    trame.append(calcul_checksum(trame))
    return bytes(trame)

def lancer_interface():
    def envoyer():
        try:
            port = entry_port.get()
            adresse = int(entry_adresse.get(), 16)
            sens = combo_sens.get()
            trame = construire_trame_ouverture(adresse, sens)
            envoyer_trame(port, trame)
        except ValueError:
            messagebox.showerror("Erreur", "Adresse invalide. Utilise un format hexadécimal (ex: 02)")

    def lire_infos():
        try:
            port = entry_port.get()
            adresse = int(entry_adresse.get(), 16)
            entree, sortie = lire_infos_entrees_sorties(port, adresse)
            if entree is not None:
                label_entree.config(text=f"Entrées : {entree}")
            if sortie is not None:
                label_sortie.config(text=f"Sorties : {sortie}")
            if entree is not None and sortie is not None:
                total = entree - sortie
                label_total.config(text=f"Sur site : {total}")
                try:
                    seuil = int(entry_seuil.get())
                    if total >= seuil:
                        envoyer_trame(port, trame_blocage_entree(adresse, 0x04))  # bloquer
                    else:
                        envoyer_trame(port, trame_blocage_entree(adresse, 0x02))  # débloquer
                except ValueError:
                    pass
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def mise_a_jour_automatique():
        lire_infos()
        root.after(2000, mise_a_jour_automatique)

    root = tk.Tk()
    root.title("Contrôle Portique Turboo")
    font_large = ("Arial", 16)

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Port COM:", font=font_large).grid(row=0, column=0, sticky=tk.W, pady=5)
    entry_port = ttk.Entry(frame, font=font_large)
    entry_port.insert(0, "COM5")
    entry_port.grid(row=0, column=1, sticky="ew")

    ttk.Label(frame, text="Adresse du portique (hex):", font=font_large).grid(row=1, column=0, sticky=tk.W, pady=5)
    entry_adresse = ttk.Entry(frame, font=font_large)
    entry_adresse.insert(0, "02")
    entry_adresse.grid(row=1, column=1, sticky="ew")

    ttk.Label(frame, text="Sens d'ouverture:", font=font_large).grid(row=2, column=0, sticky=tk.W, pady=5)
    combo_sens = ttk.Combobox(frame, values=["entree", "sortie"], font=font_large)
    combo_sens.grid(row=2, column=1, sticky="ew")
    combo_sens.current(1)

    ttk.Label(frame, text="Seuil max personnes sur site:", font=font_large).grid(row=3, column=0, sticky=tk.W, pady=5)
    entry_seuil = ttk.Entry(frame, font=font_large)
    entry_seuil.insert(0, "10")
    entry_seuil.grid(row=3, column=1, sticky="ew")

    style = ttk.Style()
    style.configure("Large.TButton", font=font_large)

    btn_envoyer = ttk.Button(frame, text="Envoyer Trame d'Ouverture", command=envoyer, style="Large.TButton")
    btn_envoyer.grid(row=4, column=0, columnspan=2, pady=10)

    btn_infos = ttk.Button(frame, text="Lire Entrées/Sorties", command=lire_infos, style="Large.TButton")
    btn_infos.grid(row=5, column=0, columnspan=2, pady=10)

    label_entree = ttk.Label(frame, text="Entrées : --", font=font_large)
    label_entree.grid(row=6, column=0, columnspan=2, pady=5)

    label_sortie = ttk.Label(frame, text="Sorties : --", font=font_large)
    label_sortie.grid(row=7, column=0, columnspan=2, pady=5)

    label_total = ttk.Label(frame, text="Sur site : --", font=font_large)
    label_total.grid(row=8, column=0, columnspan=2, pady=5)

    root.after(2000, mise_a_jour_automatique)
    root.mainloop()

if __name__ == "__main__":
    lancer_interface()
