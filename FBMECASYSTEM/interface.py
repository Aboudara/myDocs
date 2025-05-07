import tkinter as tk
import serial.tools.list_ports
from tkinter import messagebox, Toplevel
from PIL import Image, ImageTk
import winsound
from config import ADRESSES_PORTIQUES, PORT_COM_DEFAUT, PORTIQUES_INVERSÉS
from comms import (
    ouvrir_connexion, construire_trame_ouverture, construire_trame_ouverture_permanente,
    envoyer_trame, lire_infos_entrees_sorties, trame_blocage_entree, trame_reinitialisation
)

ser = None
etat_blocage= {adr: None for adr in ADRESSES_PORTIQUES}
voyants_portiques = {}
pause_update = False


def emettre_signal_sonore():
    winsound.Beep(2500, 700)

class DialogSaisie(tk.Toplevel):
    def __init__(self, parent, title, prompt, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title(title)
        self.geometry("500x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.label = tk.Label(self, text=prompt, font=("Arial", 12))
        self.label.pack(pady=10)

        self.entry = tk.Entry(self, font=("Arial", 14), show="*")
        self.entry.pack(pady=5)

        self.entry.focus_set()  # 🔵 Active le focus sur le champ de saisie (curseur actif)

        self.bouton_ok = tk.Button(self, text="OK", command=self.on_ok)
        self.bouton_ok.pack(pady=10)

        self.result = None
        parent.wait_window(self)

    def on_ok(self):
        self.result = self.entry.get()
        self.destroy()
# detection de port rs485
def port_est_present(nom_port):
    ports_disponibles = [port.device for port in serial.tools.list_ports.comports()]
    return nom_port in ports_disponibles



def verifier_mot_de_passeMaster(mot_de_passe_attendu):
    global pause_update
    pause_update = True  # 🔴 Stoppe update_all pendant le dialogue
    dialog = DialogSaisie(root, "Mot de passe", "Entrez votre mot de passe :")
    mot_saisi = dialog.result

    pause_update = False  # 🟢 Redémarre update_all juste après

    if mot_saisi is None:
        return False
    elif mot_saisi == mot_de_passe_attendu:
        return True
    else:
        messagebox.showerror("Erreur", "❌ Mot de passe incorrect.")
        return False

def fermer_interface():
    if verifier_mot_de_passeMaster("admin123"):
        root.destroy()

def afficher_popup(message, couleur):
    emettre_signal_sonore()
    popup = Toplevel(root)
    popup.overrideredirect(True)
    popup.configure(bg=couleur)
    popup.geometry("600x300+{}+{}".format(
        root.winfo_rootx() + root.winfo_width() // 2 - 300,
        root.winfo_rooty() + root.winfo_height() // 2 - 150
    ))
    label = tk.Label(popup, text=message, font=("Segoe UI", 20, "bold"), bg=couleur, fg="white")
    label.pack(expand=True, fill="both")
    root.after(2000, lambda: popup.destroy())

def envoyer(adresse, sens):
    global ser
    port = entry_port.get()

    if PORTIQUES_INVERSÉS.get(adresse, False):
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
        messagebox.showerror("Erreur", str(e))


def ouverture_permanente():
    if messagebox.askyesno("Confirmation", "Ouverture permanente à tous les portiques ?"):
        try:
            if ser and ser.is_open:
                # Utilise la connexion série déjà ouverte
                for adr in ADRESSES_PORTIQUES:
                    trame = construire_trame_ouverture_permanente(adr)
                    envoyer_trame(ser, trame)
            else:
                # Sinon ouvre une connexion temporaire
                with ouvrir_connexion(entry_port.get()) as temp_ser:
                    for adr in ADRESSES_PORTIQUES:
                        trame = construire_trame_ouverture_permanente(adr)
                        envoyer_trame(temp_ser, trame)
        except Exception as e:
            messagebox.showerror("Erreur COM", str(e))

def reinitialiser_compteurs():
    if verifier_mot_de_passeMaster("admin456"):
        if messagebox.askyesno("Confirmation", "Réinitialiser les compteurs ?"):
            try:
                # Utilise la connexion existante si elle est ouverte
                if ser and ser.is_open:
                    for adr in ADRESSES_PORTIQUES:
                        trame = trame_reinitialisation(adr)
                        envoyer_trame(ser, trame)
                else:
                    # Sinon ouvre une connexion temporaire
                    with ouvrir_connexion(entry_port.get()) as temp_ser:
                        for adr in ADRESSES_PORTIQUES:
                            trame = trame_reinitialisation(adr)
                            envoyer_trame(temp_ser, trame)
            except Exception as e:
                messagebox.showerror("Erreur COM", str(e))

def envoyer_mode_global(mode):
    port = entry_port.get()

    # Liste des portiques à appliquer la commande
    portiques_a_appliquer = []

    # Vérifier l'état des checkboxes et sélectionner les portiques

    if checkboxesNord[0x02].get() == 1:
        portiques_a_appliquer.extend([0x02])
    if checkboxesNord[0x03].get() == 1:
        portiques_a_appliquer.extend([0x03])
    if checkboxesNord[0x04].get() == 1:
        portiques_a_appliquer.extend([0x04])
    if checkboxesNord[0x05].get() == 1:
        portiques_a_appliquer.extend([0x05])
    if checkboxesEST[0x06].get() == 1:
        portiques_a_appliquer.extend([0x06])
    if checkboxesEST[0x07].get() == 1:
        portiques_a_appliquer.extend([0x07])
    if checkboxesEST[0x08].get() == 1:
        portiques_a_appliquer.extend([0x08])

    if not portiques_a_appliquer:  # Si aucun checkbox n'est sélectionné, ne faire rien
        messagebox.showerror("Erreur", f"Vous devez selectionner au moins un groupe ")
        return

    try:
        with ouvrir_connexion(port) as ser:
            for adr in portiques_a_appliquer:
                # Appliquer la commande uniquement sur les portiques sélectionnés
                mode_a_envoyer = 0x06 if mode == 0x04 and PORTIQUES_INVERSÉS.get(adr, False) else mode
                trame = trame_blocage_entree(adr, mode_a_envoyer)
                envoyer_trame(ser, trame)
    except Exception as e:
        messagebox.showerror("Erreur COM", str(e))

counter = 0  # Compteur pour alterner la mise à jour du label
def update_all():
    global ser
    if pause_update:
        root.after(2000, update_all)
        return

    port_utilise = entry_port.get()
    if not port_est_present(port_utilise):
        label_alerte_rs485.config(text="🚫 Convertisseur RS485 n'est plus détecté !")
        root.after(2000, update_all)
        return


    if not ser or not ser.is_open:
        print("⛔ Port série non connecté.")
        return

    try:
        # Dictionnaires pour stocker les entrées et sorties de chaque portique séparément
        entrees_par_portique = {adr: 0 for adr in ADRESSES_PORTIQUES}
        sorties_par_portique = {adr: 0 for adr in ADRESSES_PORTIQUES}

        portiques_hs = []

        # Boucle pour obtenir les informations de chaque portique
        for adr in ADRESSES_PORTIQUES:
            entree, sortie = lire_infos_entrees_sorties(ser, adr)

            if adr in PORTIQUES_INVERSÉS:
                entree, sortie = sortie, entree

            # Stockage des valeurs pour chaque portique (si elles sont valides et non négatives)
            if entree is not None and sortie is not None and entree >= 0 and sortie >= 0:
                entrees_par_portique[adr] = entree
                sorties_par_portique[adr] = sortie
                voyants_portiques[adr].config(bg="light green")
            else:
                portiques_hs.append(adr)
                root.after(4000, lambda: voyants_portiques[adr].config(bg="red"))

        # Vérification de l'état des portiques
        if portiques_hs:
            noms = ', '.join(str(ADRESSES_PORTIQUES.index(a) + 1) for a in portiques_hs)
            root.after(4000, lambda:label_alerte_rs485.config(text=f"🚨 Portique(s) {noms} hors ligne !"))
        else:
            label_alerte_rs485.config(text="")

        # Calcul du total des entrées et sorties
        total_entree = sum(entrees_par_portique.values())
        total_sortie = sum(sorties_par_portique.values())

        total_sur_site = total_entree - total_sortie
        if  not portiques_hs:
            root.after(4000, lambda: label_global.config(text=f"\U0001F465 Total sur site : {total_entree - total_sortie}"))


        # Gestion des seuils et affichage des popups
        seuil = int(entry_seuil.get())
        if seuil > 0 and total_sur_site / seuil >= 0.96:
            afficher_popup("⚠️ Entrées bloquées !", "red")
        elif seuil > 0 and total_sur_site / seuil >= 0.92:
            afficher_popup("⚠️ Bientôt complet !", "orange")

        # Mise à jour de l'état des portiques en fonction du total sur site
        for adr in ADRESSES_PORTIQUES:
            should_block = total_sur_site >= seuil * 0.96

            if should_block:
                # Blocage : entrée normale ou inversée
                new_state = 0x06 if adr in PORTIQUES_INVERSÉS else 0x04
            else:
                # Mode libre
                new_state = 0x02

            if etat_blocage[adr] != new_state:
                envoyer_trame(ser, trame_blocage_entree(adr, new_state))
                etat_blocage[adr] = new_state

    except Exception as e:
        print("Erreur dans update_all :", e)

    root.after(2000, update_all)

def connecter_deconnecter():
    global ser
    global etat_blocage
    port = entry_port.get()

    # Si déjà connecté → demander mot de passe avant déconnexion
    if ser and ser.is_open:
        if not verifier_mot_de_passeMaster("admin123"):
            messagebox.showinfo("Info", "Déconnexion annulée.")
            return

        try:
            ser.close()
            print("✅ Port série déconnecté proprement.")
        except:
            pass
        ser = None
        btn_connect.config(text="Se connecter", bg="#27ae60")
        return

    # Sinon, tentative de connexion
    try:
        etat_blocage = {adr: None for adr in ADRESSES_PORTIQUES}
        ser = ouvrir_connexion(port)
        btn_connect.config(text="Se déconnecter", bg="#c0392b")
        print("✅ Port série connecté.")
        update_all()
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de se connecter à {port} :\n{e}")

# Fonction activer_desactiver_seuil
def activer_desactiver_seuil():
    if entry_seuil.cget("state") == "readonly":
        if verifier_mot_de_passeMaster("admin789"):
            # Si l'Entry est en mode "readonly", on passe en mode "normal" et on cache le Label
            entry_seuil.config(state="normal")  # Passer l'Entry en mode modifiable
            label_seuil.grid_forget()# Cacher le Label
            btn_change_seuil.config(text="🔄 changer", bg="#27ae60")

    else:
        # Si l'Entry est en mode "normal", on le passe en "readonly" et on affiche le Label
        entry_seuil.config(state="readonly")  # Passer l'Entry en mode readonly
        label_seuil.config(text=entry_seuil.get())
        label_seuil.grid(row=0, column=5, padx=10)  # Réafficher le Label
        btn_change_seuil.config(text="🔄 changer seuil", bg="gray")


def lancer_interface():
    global root, entry_port, entry_seuil, label_global, btn_connect, btn_change_seuil, label_seuil, label_alerte_rs485, checkboxesNord, checkboxesEST

    root = tk.Tk()
    root.title("Contrôle d'accès FB-MecSystem")
    root.attributes('-fullscreen', True)  # Mettre la fenêtre en plein écran
    #root.protocol("WM_DELETE_WINDOW", lambda: None)
    root.configure(bg="#048B9A")
    #root.geometry("1200x800")

    font_large = ("Segoe UI", 20)
    frame = tk.Frame(root, bg="#048B9A")
    frame.pack(fill="both", expand=True)

    # 🔽 Logo entreprise
    try:
        logo_img = Image.open(r"FBMecaSystem\\FBMecaSystem1.png")
        logo_img = logo_img.resize((300, 80), Image.LANCZOS)
        logo_tk = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(frame, image=logo_tk, bg="#048B9A")
        logo_label.image = logo_tk  # Pour garder la référence
        logo_label.pack(pady=(10, 0))
    except Exception as e:
        print("Erreur chargement logo :", e)

    tk.Label(frame, text="FB Counter - Site : La Cité", font=("Segoe UI", 34, "bold"), bg="#048B9A", fg="white").pack(pady=5)

    top_frame = tk.Frame(frame, bg="#048B9A")
    top_frame.pack(pady=15)

    tk.Label(top_frame, text="Port COM:", font=font_large, bg="#048B9A", fg="white").grid(row=0, column=0, padx=10)
    entry_port = tk.Entry(top_frame, font=font_large, bg="#0F056B", fg="white", width=10)
    entry_port.insert(0, PORT_COM_DEFAUT)
    entry_port.grid(row=0, column=1, padx=10)

    btn_connect = tk.Button(top_frame, text="Se connecter", font=font_large, bg="#27ae60", fg="white", command=connecter_deconnecter)
    btn_connect.grid(row=0, column=2, padx=10)

    tk.Label(top_frame, text="Seuil global:", font=font_large, bg="#048B9A", fg="white").grid(row=0, column=3, padx=10)

    # Création de l'Entry pour le seuil global avec initialisation en mode readonly
    entry_seuil = tk.Entry(top_frame, font=("Segoe UI", 20, "bold"), bg="#0F056B", fg="white", width=4)
    entry_seuil.insert(0, "1293")
    entry_seuil.config(state="readonly")  # Mode readonly par défaut
    entry_seuil.grid(row=0, column=5, padx=10)

    # Création du Label pour afficher la valeur (initialement visible)
    label_seuil = tk.Label(top_frame, text=entry_seuil.get(), font=("Segoe UI", 22, "bold"), bg="#048B9A", fg="black")
    label_seuil.grid(row=0, column=5, padx=10)
    btn_change_seuil = tk.Button(top_frame, text="🔄 Changer Seuil", font=font_large, bg="gray", fg="white", command=lambda: activer_desactiver_seuil())
    btn_change_seuil.grid(row=0, column=7, padx=20)

    tk.Button(top_frame, text="🔓 Urgence", font=font_large, bg="red", fg="white", command=ouverture_permanente).grid(row=0, column=8, padx=20)


    middle_frame = tk.Frame(frame, bg="#048B9A")
    middle_frame.pack(pady=0)

    groupes_frame = tk.Frame(middle_frame, bg="#048B9A")
    groupes_frame.pack()


    groupe_nord = tk.Frame(groupes_frame, bg="#048B9A")
    groupe_nord.pack(side="left", padx=50)
    tk.Label(groupe_nord, text="SAS Principale", font=("Segoe UI", 22, "bold"), bg="#048B9A", fg="white").pack(pady=(10, 5))
    checkboxesNord = {}  # Dictionnaire pour stocker les checkboxes de chaque portique
    checkboxesEST = {}  # Dictionnaire pour stocker les checkboxes de chaque portique
    for i, adr in enumerate(ADRESSES_PORTIQUES[:4]):
        row = tk.Frame(groupe_nord, bg="#048B9A")
        row.pack(pady=5)
        #Ajout Checkbox Nord
        var_check_portiqueNord = tk.IntVar()
        checkbox = tk.Checkbutton(row, text=f"Activer Fonctions Portique {i+1}", font=("Segoe UI", 15, "bold"), variable=var_check_portiqueNord, onvalue=1, offvalue=0)
        checkbox.pack(side="left", padx=10)
        checkboxesNord[adr] = var_check_portiqueNord  # Ajouter la référence du checkbox dans le dictionnaire

        #tk.Label(row, text=f"Portique {i+1}", font=font_large, bg="#048B9A", fg="white").pack(side="left", padx=10)
        tk.Button(row, text="Entrée", width=8, command=lambda a=adr: envoyer(a, "entree"), bg="#0F056B", fg="white", font=font_large).pack(side="left", padx=5)
        tk.Button(row, text="Sortie", width=8, command=lambda a=adr: envoyer(a, "sortie"), bg="#0F056B", fg="white", font=font_large).pack(side="left", padx=5)
        voyant = tk.Label(row, width=2, height=1, bg="gray", relief="sunken")
        voyant.pack(side="left", padx=5)
        voyants_portiques[adr] = voyant

    groupe_est = tk.Frame(groupes_frame, bg="#048B9A")
    groupe_est.pack(side="left", padx=50)
    tk.Label(groupe_est, text="Secondaire Est", font=("Segoe UI", 22, "bold"), bg="#048B9A", fg="white").pack(pady=(10, 5))
    for i, adr in enumerate(ADRESSES_PORTIQUES[4:]):
        row = tk.Frame(groupe_est, bg="#048B9A")
        row.pack(pady=5)

        # Ajout Checkbox EST
        var_check_portiqueEST = tk.IntVar()
        checkbox = tk.Checkbutton(row, text=f"Activer Fonctions Portique {i+5}", font=("Segoe UI", 15, "bold"), variable=var_check_portiqueEST, onvalue=1, offvalue=0)
        checkbox.pack(side="left", padx=10)
        checkboxesEST[adr] = var_check_portiqueEST  # Ajouter la référence du checkbox dans le dictionnaire

        #tk.Label(row, text=f"Portique {i+5}", font=font_large, bg="#048B9A", fg="white").pack(side="left", padx=10)
        tk.Button(row, text="Entrée", width=8, command=lambda a=adr: envoyer(a, "entree"), bg="#0F056B", fg="white", font=font_large).pack(side="left", padx=5)
        tk.Button(row, text="Sortie", width=8, command=lambda a=adr: envoyer(a, "sortie"), bg="#0F056B", fg="white", font=font_large).pack(side="left", padx=5)
        voyant = tk.Label(row, width=2, height=1, bg="gray", relief="sunken")
        voyant.pack(side="left", padx=5)
        voyants_portiques[adr] = voyant
        # Frame checkbox
    CheckBox_frame = tk.Frame(frame, bg="#048B9A")
    CheckBox_frame.pack(pady=0)





    bottom_frame = tk.Frame(frame, bg="#048B9A")
    bottom_frame.pack()

    label_global = tk.Label(bottom_frame, text="\U0001F465 Total sur site : --", font=("Segoe UI", 40, "bold"), bg="#048B9A", fg="white")
    label_global.pack(pady=40)



    boutons_modes = tk.Frame(bottom_frame, bg="#048B9A")
    boutons_modes.pack(pady=10)

    tk.Button(boutons_modes, text="🔒 Entrée/Sortie Bloquée", font=font_large, width=30, bg="#800000", fg="white", command=lambda: envoyer_mode_global(0x01)).pack(side="left", padx=10, pady=30)
    tk.Button(boutons_modes, text="🔓 Entrée/Sortie Libre", font=font_large, width=30, bg="#006400", fg="white", command=lambda: envoyer_mode_global(0x02)).pack(side="left", padx=10)
    tk.Button(boutons_modes, text="🚪 Entrée Bloquée / Sortie Libre", font=font_large, width=30, bg="#FFA500", fg="black", command=lambda: envoyer_mode_global(0x04)).pack(side="left", padx=10)
    tk.Button(boutons_modes, text="🔄 Réinitialiser Compteurs", font=font_large, width=30, bg="#2C3E50", fg="white", command=reinitialiser_compteurs).pack(side="left", padx=10)


    label_alerte_rs485 = tk.Label(bottom_frame, text="", font=("Segoe UI", 18, "bold"), bg="#048B9A", fg="yellow")
    label_alerte_rs485.pack(pady=0)

    # Ajouter un bouton pour fermer l'interface
    bouton_fermer = tk.Button(root, text="×", font=("Arial", 20), command=fermer_interface, fg="red", bd=0, relief="solid", width=2, height=1)
    bouton_fermer.pack(pady=10)


    root.mainloop()
