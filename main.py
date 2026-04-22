from abc import ABC, abstractmethod
import tkinter as tk
import re
from tkinter import messagebox, ttk
from datetime import datetime


###############################################################
# CLASSES METIER (OOP)
###############################################################

# Classe Abstraite pour les Modes de Paiement
class ModePaiement(ABC):
    
    def __init__(self, montant):
        self.montant = montant

    # L'encapsulation du montant
    @property
    def montant(self):
        return self._montant

    @montant.setter
    def montant(self, m):
        if m < 0:
            raise ValueError("Le montant doit être >= 0.")
        self._montant = m

    # Méthode abstraite pour calculer les frais de transaction.
    @abstractmethod
    def calculer_frais(self):
        pass

    # Méthode abstraite pour exécuter la logique de paiement et retourne un message.
    @abstractmethod
    def payer(self):
        pass

# Classe Fille de ModePaiment: Carte Bancaire 
class CarteBancaire(ModePaiement):
    def __init__(self, montant, numero):
        super().__init__(montant)
        self.numero = numero
    
    # la méthode abstraite qui calcule les frais de transaction.
    def calculer_frais(self):
        return self.montant * 0.015  # 1.5% de frais
    
    # La méthode abstraite qui exécute la logique de paiement et retourne un message.
    def payer(self):
        # Validation du numéro de carte.
        clean_num = self.numero.replace(" ", "").replace("-", "")
        if len(clean_num) != 16 or not clean_num.isdigit():
            raise ValueError("Numéro de carte invalide (16 chiffres requis).")
        # On formate le numéro pour l'affichage.
        formatted = " ".join([clean_num[i:i+4] for i in range(0, 16, 4)])
        return f"Paiement par Carte ({formatted})"

# Classe Fille: PayPal
class PayPal(ModePaiement):
    def __init__(self, montant, email):
        super().__init__(montant)
        self.email = email

    # la méthode abstraite qui calcule les frais de transaction.
    def calculer_frais(self):
        return self.montant * 0.02  # 2% de frais

    # La méthode abstraite qui exécute la logique de paiement et retourne un message.
    def payer(self):
        # Validation de l'adresse email
        if "@" not in self.email or "." not in self.email.split("@")[1]: #******@***.***
            raise ValueError("Adresse PayPal invalide.")
        return f"Paiement via PayPal ({self.email})"

# Classe Fille: Crypto Wallet
class CryptoWallet(ModePaiement):
    def __init__(self, montant, wallet):
        super().__init__(montant)
        self.wallet = wallet

    # la méthode abstraite qui calcule les frais de transaction.
    def calculer_frais(self):
        return self.montant * 0.005  # 0.5% de frais

    # La méthode abstraite qui exécute la logique de paiement et retourne un message.
    def payer(self):
        # Validation de l'adresse (minimum 12 caractères pour la simulation)
        if len(self.wallet) < 12:
            raise ValueError("Adresse Crypto invalide (minimum 12 caractères).")
        return f"Paiement en Crypto ({self.wallet[:3]}...{self.wallet[-3:]})"# pour plus de protection

# Classe de Modélisation: Transaction (Permet de stocker un historique propre.)
class Transaction:
    
    def __init__(self, nom, mode, montant, frais):
        self.nom = nom
        self.mode = mode
        self.montant = montant
        self.frais = frais
        self.timestamp = datetime.now()
    
    # Donne une chaîne formatée pour l'affichage d'historique.
    def resume(self):
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{time_str}] {self.nom[:15]:<15} | {self.mode:15} | {self.montant:>8.2f} DH | Frais: {self.frais:>6.2f} DH"


###############################################################
# Le logique de cette app
###############################################################

# Variables globales.
transactions = [] # Liste contenant tous les objets Transaction.
Solde = 0 # Solde actuel du compte (Initialisé à 0).

# Pour formate le numéro de carte bancaire en temps réel et insère un espace entre 4 chiffres pour améliorer la lisibilité.
def format_card_number(event=None):
    # Supprime tous les espaces ou tirets déjà présents pour la méthode carte
    if var_methode.get() == "carte":
        value = entry_info.get().replace(" ", "").replace("-", "")
        if value.isdigit(): # vérification que l'entrée est bien numérique
            # Découper la chaîne par blocs de 4 chiffres, limité à 16 chiffres
            formatted = " ".join([value[i:i+4] for i in range(0, min(len(value), 16), 4)])
            # Mise à jour du champ si le format a changé
            if formatted != entry_info.get():
                entry_info.delete(0, tk.END)
                entry_info.insert(0, formatted[:19])  # Max 16 chiffres + 3 espaces

# Une fonction qui n'autoriser que les nombres décimaux. 
# P detecte seulement les chiffres et '.'.
def format_montant(P):
    if P =="": return True
    try:
        float(P)
        return True
    except ValueError:
        return False

# Calculer et afficher les données dans leur panneau.
def update_statistics():
    total_transactions = len(transactions)
    total_entrees = sum(t.montant for t in transactions if t.mode == "Dépôt")
    total_sorties = sum(t.montant for t in transactions if t.mode != "Dépôt")
    total_fees = sum(t.frais for t in transactions)
    total_debited = total_sorties + total_fees
    last_client = transactions[-1].nom if transactions else "aucune"
    stats_text = f"""
    Dernier Client: {last_client}
    Transactions: {total_transactions}
    SOLDE ACTUEL: {Solde:.2f}
    Total Déposé (+): {total_entrees:.2f} DH
    Solde Retiré (-): {total_sorties:.2f} DH
    Frais Total: {total_fees:.2f} DH
    Total Retiré: {total_debited:.2f} DH
    """
    
    label_stats.config(text=stats_text.strip())

# La fonction principale qui contient la logique de paiement et dépôt.
def effectuer_paiement():
    global Solde
    # Récupération des données
    montant_str = entry_montant.get().strip()
    nom_client = entry_name.get().strip()
    methode = var_methode.get()
    info = entry_info.get().strip().replace(" ", "").replace("-", "")
    type_op = combo_type.get()

    try:    
        # Verifier si le nom correct (contient seulement lettres,espaces et -)
        if not re.fullmatch(r'^[a-zA-Z\-\s]+$', nom_client):
            raise ValueError("Le nom est invalide.")
        # Si la case est vide.
        if not montant_str:
            raise ValueError("Veuillez entrer un montant.")
        montant = float(montant_str)
        
        # Initialisation des variables de transaction.
        frais = 0
        label = ""
        message = ""
        
        # Le logique de dépôt.
        if type_op == "Dépôt":
            frais = 0 
            Solde += montant
            message = "Dépôt effectué avec succès"
            icon = "💰"
            label = "Dépôt"
            total = montant
        
        # Le logique de paiement
        else:
            # Validation des champs de paiement.
            if methode == "":
               raise ValueError("Choisissez un mode de paiement.")
            if info == "":
               raise ValueError("Veuillez remplir le champ d'information.")
            
            # Création de l'objet de paiement.
            if methode == "carte":
               paiement = CarteBancaire(montant, info)
               label = "Carte Bancaire"
               icon = "💳"
            elif methode == "paypal":
               paiement = PayPal(montant, info)
               label = "PayPal"
               icon = "🔵"
            elif methode == "crypto":
               paiement = CryptoWallet(montant, info)
               label = "Crypto"
               icon = "₿"
            # Traitement des frais et le total
            message = paiement.payer()
            frais = paiement.calculer_frais()
            frais = round(frais, 2) 
            total = montant + frais
            total = round(total, 2)
            if total > Solde:
                raise ValueError(f"Solde insuffisant! (Votre solde: {Solde:.2f} DH)")
            Solde -= total

        # Historique
        transactions.append(Transaction(nom_client, label, montant, frais))
        maj_historique()
        update_statistics()

        # Nettoyage des entrées 
        entry_montant.delete(0, tk.END)
        entry_info.delete(0, tk.END)
        entry_name.delete(0, tk.END)
        var_methode.set("")

        # Le messagebox 
        messagebox.showinfo("✅ Opération réussi",
            
            f"{icon} {message}\n\n"
            f"Le nom : {nom_client}\n"
            f"Montant : {montant:.2f} DH\n"
            f"Frais : {frais:.2f} DH ({frais/montant*100:.2f}%)\n"
            f"Nouveau solde : {Solde:.2f} DH"
        )
    
    # Gestion des erreurs.
    except ValueError as e:
        messagebox.showerror("Erreur", str(e))
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur inattendue s'est produite:\n{str(e)}")

# Permet d'effacer les cases non importants pour le dépôt.
def toggle_payment_fields(*args):

    op_type = combo_type.get()
    if op_type == "Dépôt":
        method_label.grid_remove()
        method_frame.grid_remove() 
        info_label.grid_remove()
        entry_info.grid_remove()
        label_hint.grid_remove()
        # Déplacer le bouton de paiement vers le haut.
        btn_payment.grid(row=6, column=0, sticky="ew", pady=(10, 3), ipady=3)
    else: # Pour le paiement.
        method_label.grid()
        method_frame.grid()
        info_label.grid()
        entry_info.grid()
        label_hint.grid()
        btn_payment.grid(row=11, column=0, sticky="ew", pady=(0, 5), ipady=3)
        on_method_change() # S'assurer que le Hint est mis à jour selon la méthode de paiement sélectionnée

# Met à jour la listbox affichant l'historique des transactions.
def maj_historique():
    listbox_hist.delete(0, tk.END)
    if not transactions:
        listbox_hist.insert(tk.END, "Aucune transaction pour le moment")
        return
    # Insère les transactions dans l'ordre inverse (les plus récentes en premier)
    for t in reversed(transactions):  # Most recent first
        listbox_hist.insert(tk.END, t.resume())

# Pour effacer toutes les transactions.
def clear_history():
    if transactions:
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment effacer tout l'historique ?"):
            transactions.clear()
            maj_historique()
            update_statistics()

# Nettoie le champ d'information et met à jour le hint selon la méthode choisie.
def on_method_change(*args):
    """Clear info field and update hint when payment method changes."""
    entry_info.delete(0, tk.END)
    method = var_methode.get()
    if method == "carte":
        label_hint.config(text="**Format: 16 chiffres (ex: 1234 5678 9012 3456)")
    elif method == "paypal":
        label_hint.config(text="**Format: adresse email valide (ex: user@example.com)")
    elif method == "crypto":
        label_hint.config(text="**Format: adresse wallet (minimum 6 caractères)")
    else:
        label_hint.config(text="")


###############################################################
# INTERFACE
###############################################################

# Configuration de la fenêtre principale.
root = tk.Tk()
root.title("🏦 Application Bancaire")
root.geometry("1000x750")
root.config(bg="#0F1419")
root.resizable(False, False)

# Palette de couleurs (pour optimiser et centraliser la gestion de nos couleurs).
COLORS = {
    "bg_dark": "#0F1419",
    "bg_card": "#1A1F2E",
    "bg_input": "#252B3B",
    "bg_button": "#19944A",
    "bg_button_hover": "#5BA0F2",
    "accent": "#4A90E2",
    "accent_secondary": "#7B68EE",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B0B8C4",
    "success": "#2ECC71",
    "border": "#2D3441"}

# Header
header_frame = tk.Frame(root, bg=COLORS["bg_dark"], height=80)
header_frame.pack(fill=tk.X, padx=0, pady=0)

header_title = tk.Label(header_frame, text="🏦 Banking Payment System", bg=COLORS["bg_dark"], 
    fg=COLORS["accent"], font=("Segoe UI", 24, "bold"))
header_title.pack(pady=15)

subtitle = tk.Label(header_frame, text="Interface de paiement bancaire",
    bg=COLORS["bg_dark"], fg=COLORS["text_secondary"], font=("Segoe UI", 11))
subtitle.pack(pady=(0, 5))

# Conteneur principal
main_container = tk.Frame(root, bg=COLORS["bg_dark"])
main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

# Panneau gauche (Formulaire de Paiement)
left_panel = tk.Frame(main_container, bg=COLORS["bg_card"], relief=tk.FLAT, bd=0, width=400)
left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
left_panel.pack_propagate(False)

# Le title
panel_title = tk.Label(left_panel, text="💳 Nouveau Paiement", bg=COLORS["bg_card"],
    fg=COLORS["accent"], font=("Segoe UI", 18, "bold"))
panel_title.pack(pady=(25, 5))

# Conteneur du formulaire
form_frame = tk.Frame(left_panel, bg=COLORS["bg_card"])
form_frame.pack(padx=30, pady=10, fill=tk.BOTH, expand=False)
form_frame.columnconfigure(0,weight=1)

# Champ 1: Nom complet.
name_label = tk.Label(form_frame, text="Le nom complet", bg=COLORS["bg_card"],
    fg=COLORS["text_primary"], font=("Segoe UI", 12), anchor="w")
name_label.grid(row=0, column=0, sticky="ew", pady=(0, 3))

entry_name = tk.Entry(form_frame, width=30, font=("Segoe UI", 13),
    bg=COLORS["bg_input"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"],
    relief=tk.FLAT, bd=0, highlightthickness=2, highlightbackground=COLORS["border"], highlightcolor=COLORS["accent"])
entry_name.grid(row=1, column=0, sticky="ew", pady=(0, 15), ipady=3)

# Champ 2: Type d'opération.
type_label = tk.Label(form_frame, text="Type d'Opération", bg=COLORS["bg_card"], fg=COLORS["text_primary"], font=("Segoe UI", 12), anchor="w")
type_label.grid(row=2, column=0, sticky="ew", pady=(0, 3))

combo_type = ttk.Combobox(form_frame, values=["Retrait / Paiement", "Dépôt"], state="readonly", font=("Segoe UI", 8))
combo_type.current(0)
combo_type.grid(row=3, column=0, pady=(0, 15), sticky="ew", ipady=5)
combo_type.bind("<<ComboboxSelected>>", toggle_payment_fields)

# Champ 3: Montant.
amount_label = tk.Label(form_frame, text="Montant (DH)", bg=COLORS["bg_card"],
    fg=COLORS["text_primary"], font=("Segoe UI", 12), anchor="w")
amount_label.grid(row=4, column=0, sticky="ew", pady=(0, 3))

entry_montant = tk.Entry(form_frame, width=30, font=("Segoe UI", 13),
    bg=COLORS["bg_input"], fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"],
    relief=tk.FLAT, bd=0, highlightthickness=2, highlightbackground=COLORS["border"],
    highlightcolor=COLORS["accent"], validate="key", validatecommand=(root.register(format_montant), "%P"))
entry_montant.grid(row=5, column=0, sticky="ew", pady=(0, 15), ipady=3)

# Champ 4: Méthode de paiement (Radio buttons).
method_label = tk.Label(form_frame, text="Méthode de Paiement", bg=COLORS["bg_card"],
    fg=COLORS["text_primary"], font=("Segoe UI", 12), anchor="w")
method_label.grid(row=6, column=0, sticky="ew", pady=(0, 3))

var_methode = tk.StringVar()
var_methode.trace("w", on_method_change)

method_frame = tk.Frame(form_frame, bg=COLORS["bg_card"])
method_frame.grid(row=7, column=0, sticky="w", pady=(0, 10))

style_radio = {"bg": COLORS["bg_card"], "fg": COLORS["text_primary"], "selectcolor": COLORS["bg_card"],
    "activebackground": COLORS["bg_card"], "activeforeground": COLORS["accent"],
    "font": ("Segoe UI", 11), "cursor": "hand2"}

rb1 = tk.Radiobutton(method_frame, text="💳 Carte Bancaire", value="carte",
                     variable=var_methode, **style_radio)
rb1.pack(anchor="w", pady=3)

rb2 = tk.Radiobutton(method_frame, text="🔵 PayPal", value="paypal",
                     variable=var_methode, **style_radio)
rb2.pack(anchor="w", pady=3)

rb3 = tk.Radiobutton(method_frame, text="₿ Crypto Wallet", value="crypto",
                     variable=var_methode, **style_radio)
rb3.pack(anchor="w", pady=3)

# Champ 5: Information de paiement (Numéro/Email/Wallet)
info_label = tk.Label(form_frame, text="Informations de Paiement", bg=COLORS["bg_card"],
    fg=COLORS["text_primary"], font=("Segoe UI", 12), anchor="w")
info_label.grid(row=8, column=0, sticky="ew", pady=(0, 3))

entry_info = tk.Entry(form_frame, width=30, font=("Segoe UI", 13), bg=COLORS["bg_input"],
    fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], relief=tk.FLAT, 
    bd=0, highlightthickness=2, highlightbackground=COLORS["border"], highlightcolor=COLORS["accent"])
entry_info.grid(row=9, column=0, sticky="ew", pady=(0, 5), ipady=3)
entry_info.bind("<KeyRelease>", format_card_number)

# Champ 6: Le Hint
label_hint = tk.Label(form_frame, text="", bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
    font=("Segoe UI", 9, "italic"), anchor="w", height=1, width=50)
label_hint.grid(row=10, column=0, sticky="ew", pady=(0, 10))

# Bouton de paiement.
# Change le couleur de button.
def on_button_enter(e):
    btn_payment.config(bg=COLORS["bg_button_hover"])

def on_button_leave(e):
    btn_payment.config(bg=COLORS["bg_button"])

btn_payment = tk.Button(form_frame, text="Effectuer le Paiement", command=effectuer_paiement, 
    bg=COLORS["bg_button"], fg=COLORS["text_primary"], font=("Segoe UI", 13, "bold"), 
    relief=tk.FLAT, bd=0, cursor="hand2", padx=32, pady=3, 
    activebackground=COLORS["bg_button_hover"], activeforeground=COLORS["text_primary"])
btn_payment.grid(row=11, column=0, sticky="ew", pady=(0, 3), ipady=3)
btn_payment.bind("<Enter>", on_button_enter)
btn_payment.bind("<Leave>", on_button_leave)

# Panneau droit (historique et statistiques).
right_panel = tk.Frame(main_container, bg=COLORS["bg_card"], relief=tk.FLAT, bd=0)
right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

# Panneau de statistiques.
stats_frame = tk.Frame(right_panel, bg=COLORS["bg_input"], relief=tk.FLAT, bd=0)
stats_frame.pack(fill=tk.X, padx=20, pady=(20, 15))

stats_title = tk.Label(stats_frame, text="Statistiques", bg=COLORS["bg_input"], fg=COLORS["accent"], font=("Segoe UI", 14, "bold"))
stats_title.pack(pady=(15, 10))

label_stats = tk.Label(stats_frame,
    text="""
    Transactions: 0
    Montant Total: 0.00 DH
    Frais Total: 0.00 DH
    Total Débité: 0.00 DH
    """, bg=COLORS["bg_input"], fg=COLORS["text_secondary"], font=("Segoe UI", 11), justify=tk.LEFT)
label_stats.pack(pady=(0, 15))

# Panneau de historique.
history_title = tk.Label(right_panel, text="Historique des Transactions", bg=COLORS["bg_card"], fg=COLORS["accent"], font=("Segoe UI", 14, "bold"))
history_title.pack(pady=(0, 10))

listbox_frame = tk.Frame(right_panel, bg=COLORS["bg_card"])
listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

scrollbar = tk.Scrollbar(listbox_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

listbox_hist = tk.Listbox(listbox_frame, width=50, height=15, bg=COLORS["bg_input"],
    fg=COLORS["text_primary"], font=("Consolas", 10), relief=tk.FLAT,
    bd=0, selectbackground=COLORS["accent"], selectforeground=COLORS["text_primary"], yscrollcommand=scrollbar.set)
listbox_hist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=listbox_hist.yview)

listbox_hist.insert(tk.END, "Aucune transaction pour le moment")

# Bouton Effacer
btn_clear = tk.Button(right_panel, text="🗑️ Effacer l'Historique", command=clear_history, bg="#E74C3C",
    fg=COLORS["text_primary"], font=("Segoe UI", 10), relief=tk.FLAT, bd=0,
    cursor="hand2", padx=15, pady=8, activebackground="#C0392B", activeforeground=COLORS["text_primary"])
btn_clear.pack(pady=(0, 20))

update_statistics()

root.mainloop()