import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess, webbrowser, mysql.connector, ctypes, sys, json, hashlib

# Vérifier si le script est exécuté en tant qu'administrateur
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Si le script n'est pas exécuté en tant qu'administrateur, relancer en tant qu'administrateur
if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


class StartPage(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Choix d'action")
        self.geometry("400x200")
        self.resizable(False, False)

        self.controller = Controller()  # Create an instance of the controller

        self.controller.selected_pc_id = None
        self.controller.selected_group_name = None

        label = tk.Label(self, text="Que voulez-vous faire ?", font=('Times', '20'))
        label.pack(pady=20)

        inventoriser_button = tk.Button(self, text="Inventoriser", command=self.inventoriser_selected)
        inventoriser_button.pack(pady=10)

        choisir_button = tk.Button(self, text="Choisir un PC existant", command=self.choisir_selected)
        choisir_button.pack(pady=10)

    def inventoriser_selected(self):
        # Lorsque l'utilisateur choisit d'inventoriser, on ouvre la page principale
        self.destroy()
        app = SelectGroupPage(controller=self.controller)
        app.mainloop()

    def choisir_selected(self):
        # Lorsque l'utilisateur choisit de choisir un PC existant, on ouvre la page de sélection
        self.destroy()
        app = SelectExistingPCPage(controller=self.controller)
        app.mainloop()

class AppPage(tk.Tk):
    def __init__(self, controller, idPC_temp=None, nomGroupe_temp=None):
        super().__init__()

        self.controller = controller
        self.controller.selected_pc_id = idPC_temp
        self.controller.selected_group_name = nomGroupe_temp
        self.title(f"Page principale - PC {self.controller.selected_pc_id} - Groupe {self.controller.selected_group_name}")
        self.geometry("900x450")
        self.resizable(True, True)


        # Créer un widget de type onglets
        tab_control = ttk.Notebook(self)
        tab_control.pack(expand=1, fill="both")

        # Créer les trois onglets
        info_tab = InfoPage(tab_control, controller=self.controller)
        installation_tab = InstallationPage(tab_control, controller=self.controller)

        # Ajouter les onglets au widget de type onglets
        tab_control.add(info_tab, text="Informations sur le PC et gestion de la BDD")
        tab_control.add(installation_tab, text="Installation de logiciels")

        # ajoute un bouton pour lancer la fonction de fin de l'application
        quitter_button = tk.Button(self, text="Quitter", command=self.quitter)
        quitter_button.pack(pady=10)

    def quitter(self):
        # propose de quitter l'application
        confirm_quit = messagebox.askyesno("Quitter", "Voulez-vous quitter l'application ?")
        # si l'utilisateur confirme, on demande si il souhaite éjecter la clé usb
        if confirm_quit:
            confirm_eject = messagebox.askyesno("Ejecter la clé USB", "Voulez-vous éjecter la clé USB ?")
            if confirm_eject:
                #on lance le programme d'éjection de clé usb powershell
                subprocess.run(["C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "C:\\Users\\kilia\\Desktop\\stage\\test-stage\\retirerUSB.ps1"])
            self.destroy()

class SelectGroupPage(tk.Tk):
    def __init__(self, controller):
        super().__init__()

        self.title("Sélectionner un groupe")
        self.geometry("720x550")
        self.resizable(False, False)

        self.controller = controller

        label = tk.Label(self, text="Sélectionnez un groupe", font=('Times', '20'))
        label.pack(pady=20)

        # Create a listbox to display groups with a scrollbar
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.group_listbox = tk.Listbox(self, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.group_listbox.yview)
        self.group_listbox.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Add a button to select the chosen group
        select_button = tk.Button(self, text="Sélectionner", command=self.select_group)
        select_button.pack(pady=10)

        # Load groups from the database
        self.load_groups()

    def load_groups(self):
        # Connect to the MySQL database
        conn = mysql.connector.connect(
            user='root',
            password='',
            host='127.0.0.1',
            database='base_test_stage',
            port='3308'
        )
        cursor = conn.cursor()
        
        # Retrieve groups from the database
        cursor.execute("SELECT idGroupe, nomGroupe FROM groupe")
        groups = cursor.fetchall()
        
        # Display groups in the listbox
        for group in groups:
            self.group_listbox.insert(tk.END, f"Groupe {group[0]} - {group[1]}")


    def select_group(self):
        # Retrieve the selected group from the listbox
        selected_index = self.group_listbox.curselection()
        
        # Store the selected group name in the controller
        if selected_index:
            selected_group_text = self.group_listbox.get(selected_index)
            selected_group_id = int(selected_group_text.split(" ")[1])  # Extract the group ID from the text
            selected_group_name = selected_group_text.split(" - ")[1]  # Extract the group name from the text
        
        # Show a dialog box to choose PC mode
        pc_mode = simpledialog.askstring("Mode PC", "Choisissez le mode d'installation du PC (neuf/non), neuf signifie que la date d'installation est aujourd'hui, sinon elle est nulle:")
        if pc_mode=="":
            pc_mode = "Non_rempli"
        loc_pc = simpledialog.askstring("Localisation PC", "Entrez la localisation du PC (vous pouvez ne rien écrire):")
        if loc_pc=="":
            loc_pc = "Non_rempli"
        compte_ms = simpledialog.askstring("Compte Microsoft", "Entrez le compte Microsoft (vous pouvez ne rien écrire):")
        if compte_ms=="":
            compte_ms = "Non_rempli"
        licence_office = simpledialog.askstring("Licence Office", "Entrez la licence Office (vous pouvez ne rien écrire):")
        if licence_office=="":
            licence_office = "Non_rempli"
        
        # Run the PowerShell script with selected parameters
        self.run_powershell_inventaire(pc_mode, selected_group_name, loc_pc, compte_ms, licence_office)

    def run_powershell_inventaire(self, pc_mode, selected_group_name, loc_pc, compte_ms, licence_office):
        # Execute the PowerShell script with selected parameters
        subprocess.run(["C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "C:\\Users\\kilia\\Desktop\\stage\\test-stage\\inventaire.ps1", pc_mode, selected_group_name, loc_pc, compte_ms])

        #recuperer l'id du pc nouvellement créé
        conn = mysql.connector.connect(
            user='root',
            password='',
            host='127.0.0.1',
            database='base_test_stage',
            port='3308'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT max(idPC) FROM pc;")
        id_pc = cursor.fetchone()
        id_pc = id_pc[0]

        #retourner sur la page principale
        app = AppPage(self.controller, id_pc, selected_group_name)
        self.destroy()
        app.mainloop()

    
class SelectExistingPCPage(tk.Tk):
    def __init__(self, controller):
        super().__init__()

        self.title("Sélectionner un PC existant")
        self.geometry("720x550")
        self.resizable(False, False)
        self.controller = controller  # Ajout du contrôleur

        label = tk.Label(self, text="Sélectionnez un PC existant", font=('Times', '20'))
        label.pack(pady=20)

        # Create a listbox to display PCs with a scrollbar
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.pc_listbox = tk.Listbox(self, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.pc_listbox.yview)
        self.pc_listbox.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Add a button to select the chosen PC
        select_button = tk.Button(self, text="Sélectionner", command=self.select_pc)
        select_button.pack(pady=10)

        # Load PCs from the database
        self.load_pcs()

    def load_pcs(self):
        # Connexion à la base de données MySQL
        conn = mysql.connector.connect(
            user='root',
            password='',
            host='127.0.0.1',
            database='base_test_stage',
            port='3308'
        )
        cursor = conn.cursor()

        # Récupérer les PC depuis la base de données
        cursor.execute("SELECT idPC, nomPC, nomGroupe FROM pc INNER JOIN groupe ON pc.idGroupe = groupe.idGroupe order by groupe.nomGroupe, pc.nomPC")
        pcs = cursor.fetchall()

        # Afficher les PC en grand dans la listbox
        for pc in pcs:
            self.pc_listbox.insert(tk.END, f"PC {pc[0]} - {pc[1]} - Groupe: {pc[2]}")

    def select_pc(self):
        # Récupérer l'élément sélectionné dans la listbox
        selected_index = self.pc_listbox.curselection()

        if selected_index:
            selected_pc_text = self.pc_listbox.get(selected_index)
            selected_pc_id = int(selected_pc_text.split(" ")[1])  # Extraire l'ID du PC à partir du texte
            selected_group_name = selected_pc_text.split("Groupe: ")[1]  # Extraire le nom du groupe à partir du texte

            # Conserver l'ID du PC et le nom du groupe dans le controller
            self.controller.selected_pc_id = selected_pc_id
            self.controller.selected_group_name = selected_group_name

            # Passer à la page principale
            app = AppPage(self.controller,selected_pc_id,selected_group_name)
            self.destroy()
            app.mainloop()
        else:
            messagebox.showwarning("Attention", "Aucun PC sélectionné.")

class Controller:
    def __init__(self):
        self.selected_pc_id = None
        self.selected_group_name = None

class InstallationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller

        label = tk.Label(self, text="Page d'installation des logiciels", font=('Times', '20'))
        label.grid(row=0, columnspan=2, pady=10, padx=10)

        # Ajouter un bouton pour installer AnyDesk en demandant s'il faut changer le mot de passe
        install_anydesk_button = tk.Button(self, text="Installer AnyDesk", command=lambda: self.install_anydesk("install"))
        install_anydesk_button.grid(row=1, column=0, pady=10, padx=10)

        # Ajouter un bouton pour changer le mot de passe AnyDesk
        change_anydesk_password_button = tk.Button(self, text="Changer le mot de passe AnyDesk (uniquement si Anydesk est déjà installé)", command=lambda: self.install_anydesk("change"))
        change_anydesk_password_button.grid(row=1, column=1, pady=10, padx=10)

    def install_anydesk(self,mode):        

        pcId = str(self.controller.selected_pc_id)
        # Ouvrir une boîte de dialogue pour entrer le mot de passe, vérifier si le mot de passe est valide (8 caractères, 1 majuscule, 1 minuscule, 1 chiffre)
        password = simpledialog.askstring("Mot de passe AnyDesk", "Entrez le mot de passe AnyDesk:")
        if password:
            if len(password) < 8:
                messagebox.showerror("Erreur", "Le mot de passe doit contenir au moins 8 caractères.")
            elif not any(char.isdigit() for char in password):
                messagebox.showerror("Erreur", "Le mot de passe doit contenir au moins un chiffre.")
            elif not any(char.isupper() for char in password):
                messagebox.showerror("Erreur", "Le mot de passe doit contenir au moins une majuscule.")
            elif not any(char.islower() for char in password):
                messagebox.showerror("Erreur", "Le mot de passe doit contenir au moins une minuscule.")
            else:
                if mode == "change":
                    self.run_powershell_install_anydesk("mdp",pcId, password)
                else:
                    self.run_powershell_install_anydesk("tout",pcId, password)
        else:
            messagebox.showerror("Erreur", "Mot de passe invalide.")

    def run_powershell_install_anydesk(self, mode, pcId, password):
        subprocess.run(["C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "C:\\Users\\kilia\\Desktop\\stage\\test-stage\\install_anydesk.ps1", mode, pcId, password])


class InfoPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.info_entries = {}  # Initialisation de l'attribut info_entries

        label = tk.Label(self, text="Informations sur le PC", font=('Times', '20'))
        label.pack(pady=10, padx=10)

        
        # Créer un canevas pour ajouter la barre de défilement
        self.canvas = tk.Canvas(self)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Créer un cadre pour contenir les éléments
        self.inner_frame = tk.Frame(self.canvas)

        # Configurer le canevas pour que la zone déroulante soit le cadre intérieur
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor=tk.NW)
        
        self.load_pc_info()

    def load_pc_info(self):
        # Supprimer tous les anciens widgets du cadre intérieur
        for widget in self.inner_frame.winfo_children():
            widget.destroy()


        # Ajouter un bouton pour enregistrer les modifications
        save_button = tk.Button(self.inner_frame, text="Enregistrer les modifs dans la BDD", command=self.save_changes)
        save_button.grid(row=2, column=0, pady=10)

        # Ajouter un bouton pour charger les informations du PC
        load_button = tk.Button(self.inner_frame, text="Recharger les infos depuis la BDD", command=self.load_pc_info)
        load_button.grid(row=2, column=1, pady=10)

        # Button to open a dialog box and add a group to the database
        add_group_button = tk.Button(self.inner_frame, text="Ajouter un groupe dans la BDD", command=self.add_group)
        add_group_button.grid(row=2, column=2, pady=10)

        # Button to open a web browser and navigate to localhost/inventaire
        open_browser_button = tk.Button(self.inner_frame, text="Ouvrir le site de gestion de la BDD", command=self.open_browser)
        open_browser_button.grid(row=2, column=3, pady=10)

        # Retrieve data from the database based on selected_pc_id
        conn = mysql.connector.connect(
            user='root',
            password='',
            host='127.0.0.1',
            database='base_test_stage',
            port='3308'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pc WHERE idPC = %s", (self.controller.selected_pc_id,))
        data = cursor.fetchone()
        nomPC = data[1]
        datePrepa = data[2]
        data = json.loads(data[3])

        

        nomPC_label = tk.Label(self.inner_frame, text=f"Nom du PC: {nomPC}")
        nomPC_label.grid(row=5, column=0, pady=5, padx=5, sticky="e")

        modif_nom_pc = tk.Button(self.inner_frame, text="Changer le nom du PC", command=self.change_pc_name)
        modif_nom_pc.grid(row=5, column=1, pady=5, padx=5, sticky="w")

        datePrepa_label = tk.Label(self.inner_frame, text=f"Date de préparation: {datePrepa}")
        datePrepa_label.grid(row=6, column=0, pady=5, padx=5, sticky="e")

        modif_date_prepa = tk.Button(self.inner_frame, text="Changer la date de préparation", command=self.change_date_prepa)
        modif_date_prepa.grid(row=6, column=1, pady=5, padx=5, sticky="w")


        label_locPC = tk.Label(self.inner_frame, text="Localisation du PC:")
        label_locPC.grid(row=7, column=0, pady=5, padx=5, sticky="e")
        entry_locPC = tk.Entry(self.inner_frame, width=35)
        entry_locPC.insert(0, data['locPC'])
        entry_locPC.grid(row=7, column=1, pady=5, padx=5, sticky="w")
        self.info_entries["locPC"] = entry_locPC

        label_userPC = tk.Label(self.inner_frame, text="Utilisateur du PC:")
        label_userPC.grid(row=8, column=0, pady=5, padx=5, sticky="e")
        entry_userPC = tk.Entry(self.inner_frame, width=35)
        entry_userPC.insert(0, data['userPC'])
        entry_userPC.grid(row=8, column=1, pady=5, padx=5, sticky="w")
        self.info_entries["userPC"] = entry_userPC

        label_compteMS = tk.Label(self.inner_frame, text="Compte Microsoft:")
        label_compteMS.grid(row=9, column=0, pady=5, padx=5, sticky="e")
        entry_compteMS = tk.Entry(self.inner_frame, width=35)
        entry_compteMS.insert(0, data['compteMicrosoft'])
        entry_compteMS.grid(row=9, column=1, pady=5, padx=5, sticky="w")
        self.info_entries["compteMicrosoft"] = entry_compteMS

        label_marquePC = tk.Label(self.inner_frame, text="Marque du PC:")
        label_marquePC.grid(row=10, column=0, pady=5, padx=5, sticky="e")
        entry_marquePC = tk.Entry(self.inner_frame, width=35)
        entry_marquePC.insert(0, data['marquePC'])
        entry_marquePC.grid(row=10, column=1, pady=5, padx=5, sticky="w")
        self.info_entries["marquePC"] = entry_marquePC

        label_modelePC = tk.Label(self.inner_frame, text="Modèle du PC:")
        label_modelePC.grid(row=11, column=0, pady=5, padx=5, sticky="e")
        entry_modelePC = tk.Entry(self.inner_frame, width=35)
        entry_modelePC.insert(0, data['modelePC'])
        entry_modelePC.grid(row=11, column=1, pady=5, padx=5, sticky="w")
        self.info_entries["modelePC"] = entry_modelePC

        label_ramPC = tk.Label(self.inner_frame, text="RAM du PC (en Go):")
        label_ramPC.grid(row=12, column=0, pady=5, padx=5, sticky="e")
        entry_ramPC = tk.Entry(self.inner_frame, width=35)
        entry_ramPC.insert(0, data['ramPC'])
        entry_ramPC.grid(row=12, column=1, pady=5, padx=5, sticky="w")
        self.info_entries["ramPC"] = entry_ramPC

        label_stockagePC = tk.Label(self.inner_frame, text="Stockage du PC (en Go):")
        label_stockagePC.grid(row=5, column=2, pady=5, padx=5, sticky="e")
        entry_stockagePC = tk.Entry(self.inner_frame, width=35)
        entry_stockagePC.insert(0, data['stockagePC'])
        entry_stockagePC.grid(row=5, column=3, pady=5, padx=5, sticky="w")
        self.info_entries["stockagePC"] = entry_stockagePC

        label_processorPC = tk.Label(self.inner_frame, text="Processeur du PC:")
        label_processorPC.grid(row=6, column=2, pady=5, padx=5, sticky="e")
        entry_processorPC = tk.Entry(self.inner_frame, width=35)
        entry_processorPC.insert(0, data['processeurPC'])
        entry_processorPC.grid(row=6, column=3, pady=5, padx=5, sticky="w")
        self.info_entries["processeurPC"] = entry_processorPC

        label_osPC = tk.Label(self.inner_frame, text="Version de Windows:")
        label_osPC.grid(row=7, column=2, pady=5, padx=5, sticky="e")
        entry_osPC = tk.Entry(self.inner_frame, width=35)
        entry_osPC.insert(0, data['versionWindows'])
        entry_osPC.grid(row=7, column=3, pady=5, padx=5, sticky="w")
        self.info_entries["versionWindows"] = entry_osPC

        label_licenceWindows = tk.Label(self.inner_frame, text="Licence Windows du PC:")
        label_licenceWindows.grid(row=8, column=2, pady=5, padx=5, sticky="e")
        entry_licenceWindows = tk.Entry(self.inner_frame, width=35)
        entry_licenceWindows.insert(0, data['licenceWindows'])
        entry_licenceWindows.grid(row=8, column=3, pady=5, padx=5, sticky="w")
        self.info_entries["licenceWindows"] = entry_licenceWindows

        label_versionOffice = tk.Label(self.inner_frame, text="Version Office du PC:")
        label_versionOffice.grid(row=9, column=2, pady=5, padx=5, sticky="e")
        entry_versionOffice = tk.Entry(self.inner_frame, width=35)
        entry_versionOffice.insert(0, data['versionOffice'])
        entry_versionOffice.grid(row=9, column=3, pady=5, padx=5, sticky="w")
        self.info_entries["versionOffice"] = entry_versionOffice

        label_licenceOffice = tk.Label(self.inner_frame, text="Licence Office du PC:")
        label_licenceOffice.grid(row=10, column=2, pady=5, padx=5, sticky="e")
        entry_licenceOffice = tk.Entry(self.inner_frame, width=35)
        entry_licenceOffice.insert(0, data['licenceOffice'])
        entry_licenceOffice.grid(row=10, column=3, pady=5, padx=5, sticky="w")
        self.info_entries["licenceOffice"] = entry_licenceOffice

        label_idAnydesk = tk.Label(self.inner_frame, text="ID AnyDesk du PC:")
        label_idAnydesk.grid(row=11, column=2, pady=5, padx=5, sticky="e")
        entry_idAnydesk = tk.Entry(self.inner_frame, width=35)
        entry_idAnydesk.insert(0, data['idAnydesk'])
        entry_idAnydesk.grid(row=11, column=3, pady=5, padx=5, sticky="w")
        self.info_entries["idAnydesk"] = entry_idAnydesk

        label_mdpAnydesk = tk.Label(self.inner_frame, text="Mot de passe AnyDesk du PC:")
        label_mdpAnydesk.grid(row=12, column=2, pady=5, padx=5, sticky="e")
        entry_mdpAnydesk = tk.Entry(self.inner_frame, width=35)
        entry_mdpAnydesk.insert(0, data['mdpAnydesk'])
        entry_mdpAnydesk.grid(row=12, column=3, pady=5, padx=5, sticky="w")
        self.info_entries["mdpAnydesk"] = entry_mdpAnydesk

            
    def change_pc_name(self):
        # Ouvrir une boîte de dialogue pour changer le nom du PC
        new_pc_name = simpledialog.askstring("Changer le nom du PC", "Entrez le nouveau nom du PC:")
        if new_pc_name:
            # Connect to the MySQL database
            conn = mysql.connector.connect(
                user='root',
                password='',
                host='127.0.0.1',
                database='base_test_stage',
                port='3308'
            )
            cursor = conn.cursor()
            cursor.execute("UPDATE pc SET nomPC = %s WHERE idPC = %s", (new_pc_name, self.controller.selected_pc_id))
            conn.commit()
            messagebox.showinfo("Succès", "Le nom du PC a été modifié avec succès.")
            self.load_pc_info()
        else:
            messagebox.showerror("Erreur", "Nom de PC invalide.")

    def change_date_prepa(self):
        # Ouvrir une boîte de dialogue pour changer la date de préparation
        # exemple d'une date valide: "1957-01-02 23:51:14"
        # demande de l'année
        new_annee_prepa = simpledialog.askstring("Changer la date de préparation", "Entrez la nouvelle année de préparation:")
        # demande du mois
        new_mois_prepa = simpledialog.askstring("Changer la date de préparation", "Entrez le nouveau mois de préparation:")
        # demande du jour
        new_jour_prepa = simpledialog.askstring("Changer la date de préparation", "Entrez le nouveau jour de préparation:")
        # demande de l'heure
        new_heure_prepa = simpledialog.askstring("Changer la date de préparation", "Entrez la nouvelle heure de préparation:")
        # demande des minutes
        new_minute_prepa = simpledialog.askstring("Changer la date de préparation", "Entrez la nouvelle minute de préparation:")
        # si toutes les valeurs sont valides, c'est à dire si elles contiennent 2 caractères, sauf l'année qui en contient 4, on les concatène pour former la date de préparation
        if new_annee_prepa and new_mois_prepa and new_jour_prepa and new_heure_prepa and new_minute_prepa:
            if len(new_annee_prepa) != 4:
                messagebox.showerror("Erreur", "Année invalide.")
            if len(new_mois_prepa) != 2:
                messagebox.showerror("Erreur", "Mois invalide.")
            if len(new_jour_prepa) != 2:
                messagebox.showerror("Erreur", "Jour invalide.")
            if len(new_heure_prepa) != 2:
                messagebox.showerror("Erreur", "Heure invalide.")
            new_date_prepa = new_annee_prepa + "-" + new_mois_prepa + "-" + new_jour_prepa + " " + new_heure_prepa + ":" + new_minute_prepa + ":00"
            
        conn = mysql.connector.connect(
            user='root',
            password='',
            host='127.0.0.1',
            database='base_test_stage',
            port='3308'
        )
        cursor = conn.cursor()
        cursor.execute("UPDATE pc SET datePrepaPC = %s WHERE idPC = %s", (new_date_prepa, self.controller.selected_pc_id))
        conn.commit()
        messagebox.showinfo("Succès", "La date de préparation a été modifiée avec succès.")
        self.load_pc_info()        

    def save_changes(self):
        # Connect to the MySQL database
        conn = mysql.connector.connect(
            user='root',
            password='',
            host='127.0.0.1',
            database='base_test_stage',
            port='3308'
        )
        cursor = conn.cursor()

        # Update the data in the database based on the selected_pc_id
        data = {}
        for key, entry in self.info_entries.items():
            data[key] = entry.get()
        data = json.dumps(data)
        cursor.execute("UPDATE pc SET dataPC = %s WHERE idPC = %s", (data, self.controller.selected_pc_id))
        conn.commit()
        messagebox.showinfo("Succès", "Les modifications ont été enregistrées avec succès.")

    def add_group(self):
        # Connexion à la base de données MySQL
        conn = mysql.connector.connect(
            user='root',
            password='',
            host='127.0.0.1',
            database='base_test_stage',
            port='3308'
        )
        cursor = conn.cursor()
        group_name = simpledialog.askstring("Ajouter un groupe", "Entrez le nom du groupe:")

        if group_name:
            # Vérifier si le groupe existe
            cursor.execute("SELECT * FROM groupe WHERE nomGroupe = %s", (group_name,))
            group_record = cursor.fetchone()

            if group_record:
                messagebox.showerror("Erreur", "Le groupe existe déjà.")
            else:
                cursor.execute("INSERT INTO groupe (nomGroupe) VALUES (%s)", (group_name,))
                conn.commit()
                messagebox.showinfo("Succès", "Le groupe a été ajouté avec succès.")
        else:
            messagebox.showerror("Erreur", "Nom de groupe invalide.")

    def open_browser(self):
        url = "http://localhost/inventaire"
        webbrowser.open(url)


if __name__ == "__main__":
    app = StartPage()
    app.mainloop()
