#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pytesseract import pytesseract
from tkcalendar import DateEntry
from pattern_matcher import *
from tesseract import *
import bdd_SQL
from openai_deepl import *
import pymupdf
from rapidAPI import *


# Crée le folder temporaire pour les fichiers intermédiaires
temp_folder = "factures_temporaire"  # nom du dossier de sortie
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)  # crée le dossier s'il n'existe pas

# Suppression du répertoire temporaire (utilisé lors de la sortie de l'UI)
def cleanup():
    # Chemin du répertoire temporaire dans le répertoire courant
    temp_dir_path = os.path.join(os.getcwd(), temp_folder)
    # Vérifie si le répertoire existe
    if os.path.exists(temp_dir_path):
        try:
            # Supprime le répertoire et son contenu
            shutil.rmtree(temp_dir_path)
            # Affiche un message de succès
       #     messagebox.showinfo("suppression", "le répertoire 'factures_temporaire' "
       #                                        "a été supprimé avec succès.")
            print("le répertoire 'factures_temporaire' a été supprimé avec succès.")

        except Exception as e:
            # Affiche un message d'erreur en cas de problème
            messagebox.showerror("erreur de suppression",
                                 f"une erreur est survenue lors de la suppression du répertoire "
                                 f"'factures_temporaire': {e}")
            
# Lorsque l'UI est fermée
def on_close():
    # Appelle la fonction de nettoyage
    cleanup()
    # Ferme la fenêtre de tkinter
    root.destroy()



# Variables globales de l'UI
width_ui = 1500             # Largeur de l'UI
height_ui = 900             # Hauteur de l'UI
max_width_image = 750       # Largeur max du canvas à afficher sur l'UI
max_height_image = 880      # Hauteur max du canvas à afficher sur l'UI
print("largeur de l'UI: ", width_ui)
print("hauteur de l'UI: ", height_ui)
print("largeur max du canvas: ", max_width_image)
print("largeur  max du canvas: ", max_height_image)
padding_x_first_r = (200, 30)   # Utilisé pour l'onglet comptabilité
padding_x_acc = 30              # Utilisé pour l'onglet comptabilité
padding_x_0 = (10, 0)           # Utilisé pour l'onglet 2 (validation des détails de la facture)
padding_x_1 = (5, 0)            # Utilisé pour l'onglet 2 (validation des détails de la facture)
padding_x_2 = (5, 10)           # Utilisé pour l'onglet 2 (validation des détails de la facture)
padding_y = (5, 0)              # Utilisé pour l'onglet 2 (validation des détails de la facture)
padding_y_fin = (5, 20)         # Utilisé pour l'onglet 2 (validation des détails de la facture)
Var_stockage_cate = ""
# Variable qui sert a effacer la TAB3 si elle est activé ( je n'ai pas trouvé d'autre solution
# pour vérifier si la TAB 3 est activée ou non)
global TAB3_etat
TAB3_etat=0
img_cv = None  # Image chargée dans opencv pour le traitement

rectangles = []  # Liste des rectangles dessinés sur le canvas

# Liste des catégories de dépenses
# DOIT ETRE EN LIGNE AVEC pattern_matcher fonction get_category
liste_categorie_depense = ('Ameublement', 'Alimentaire', 'Assurances', 'Bar', 'Bricolage',
                           'Cosmétiques', 'Électronique', 'Frais bancaires', 'Livres', 'Logement',
                           'Loisirs', 'Prêt-à-porter', 'Restauration', 'Santé', 'Service',
                           'Services Publics', 'Sport', 'Téléphonie', 'Transport', 'Travaux',
                           'Autre')

# Nombre de types de dépenses
length_expense_category = len(liste_categorie_depense)

# Liste des principales devises de pays francophones + USD
liste_devises	= ('EUR', 'CHF', 'CAD', 'XOF', 'XAF', 'XPF', 'RWF',
                    'CDF', 'KMF', 'GNF', 'BIF', 'DJF', 'USD', 'Autre')


# Listes des montants cumulés pour chaque catégorie pour les périodes n et n-1
somme_montant_cat_year_n = []  # Période n
somme_montant_cat_year_n_1 = []  # Période n-1

# Initialise les listes avec des valeurs nulles
for i in range(length_expense_category):
    somme_montant_cat_year_n.append(None)
    somme_montant_cat_year_n_1.append(None)


# *** FONCTIONS LIÉES AUX ONGLETS 1, 2 ET 3 (LECTURE, VÉRIFICATION, ENREGISTREMENT ET
# TRADUCTION D'UNE FACTURE) *****

# Initialise les variables globales pour chaque facture
def initialisation():
    global min_rescale_factor, rectangles, rect_id, img_cv, base_name, \
        file_name_without_extension,  \
        texte_nettoye, texte_corrige, file_path, file_path_display, file_extension,  \
        chemin_fichier_temp_traduit, count
    global issuer, date_format_dd_mm_yyyy, date, amount, currency, fx_rate, amount_eur, expense_category, \
        language, id_facture, flag_champs_oblig, flag_champs_obligatoires, description_champs_obligatoires
    global photo, w, h, w_r, h_r

    # Efface les rectangles dessinés sur le canvas
    while rectangles:
        clear_last_rectangle()

    # Réinitialise les variables globales (utilisé à chaque chargement d'une nouvelle facture)
    photo = None
    min_rescale_factor = 1  # Facteur de redimensionnement de l'image pour affichage dans l'UI
    w = 0  # Largeur de l'image
    h = 0  # Hauteur de l'image
    w_r = 0  # Largeur de l'image redimensionnée pour affichage dans l'UI
    h_r = 0  # Hauteur de l'image redimensionnée pour affichage dans l'UI

    rect_id = None  # Identifiant du rectangle en cours de dessin

    img_cv = None  # Image chargée dans opencv pour le traitement
    file_path = None       # Chemin complet de la facture initiale chargée dans l'onglet 1
    file_path_display = None  # Chemin de la facture modifiée initialement chargée dans l'onglet 1, modifiée avant affichage
    base_name = None  # Nom de base de la facture initiale chargée dans l'onglet 1, avec extension
    file_name_without_extension = None  # Nom de base de la facture initiale chargée dans l'onglet 1, sans extension
    file_extension = None  # Extension de la facture initiale chargée dans l'onglet 1
    chemin_fichier_temp_traduit = None  # Fichier temp pour sauvegarder le texte après traduction automatique
    texte_nettoye = None  # Texte après nettoyage automatique
    texte_corrige = None  # Texte après corrections de l'utilisateur
    
    issuer = None  # Emetteur de la facture
    date_format_dd_mm_yyyy = None  # Date de la facture au format dd-mm-yyyy (pour lecture utilisateur)
    date = None  # Date de la facture au format yyyy-mm-dd (format dans la base de données)
    amount = 0  # Montant total de la facture en devise
    currency = None  # Devise de la facture
    amount_eur = 0  # Montant total de la facture en euros
    expense_category = None  # Catégorie de dépense

    language = None  # Langue vers laquelle la traduction est demandée
    id_facture = 0  # Identifiant unique pour chaque facture
    flag_champs_obligatoires = [0, 0, 0, 0, 0]  # Indicateurs des champs obligatoires remplis
    description_champs_obligatoires = [         # Correspondance de chaque indice de la variable flag_champs_obligatoires
        'émetteur',
        'date de la facture',
        'montant en devise',
        'devise',
        'catégorie de dépense'
    ]

    # Efface le contenu des champs de l'UI:
    issuer_label.set(issuer)
    date_label.set(date)
    amount_label.set(amount)
    currency_label.set(currency)
    issuer_entry.delete(0, "end")
    date_entry.delete(0, "end")
    amount_entry.delete(0, "end")
    currency_entry.delete(0, "end")
    amount_eur_confirmed.set(amount_eur)
    expense_category_label.set(expense_category)
    expense_category_entry.delete(0, "end")
    text_widget.delete(1.0, tk.END)
    language_entry.delete(0, "end")

    # Active ou désactive le bouton de validation des éléments-clés de l'onglet 2:
    button_validate_main_data.config(state="active")
    button_validate_text.config(state="disabled")
    button_view_text.config(state="disabled")  
    button_translate.config(state="disabled")

    # Désactive l'onglet 2
    tab_control.tab(1, state='disabled')


# Fonction pour afficher le mode d'emploi des rectangles (lié à l'onglet 1)
def manuel_utilisation_tab_1():
    global width_ui, height_ui
    # Ouvre une nouvelle fenêtre
    tab_man_util_tab1 = tk.Toplevel(root)
    size_ui = str(width_ui) + 'x' + str(height_ui)
    # Dimension de la fenêtre
    tab_man_util_tab1.geometry(size_ui)
    # Titre de la fenêtre
    tab_man_util_tab1.title("Manuel d'utilisation")

    # Ouvre l'image mode d'emploi avec PIL
    img_manuel_util = Image.open("facture1_assistance.jpg")

    # Redimensionne l'image pour affichage complet
    w_man_util, h_man_util = img_manuel_util.size
    resized_image_manuel_util = (img_manuel_util.resize((int(w_man_util * 0.8),
                                                         int(h_man_util * 0.8)), resample=0))
    # Convertit l'image PIL en image Tkinter
    photo_manuel_util = ImageTk.PhotoImage(resized_image_manuel_util)

    panel = tk.Label(tab_man_util_tab1, image=photo_manuel_util, background="#333333", foreground="white",)
    panel.image = photo_manuel_util
    panel.pack()


# Fonction pour importer une image depuis le système de fichiers (onglet 1)
def import_image():
    global img_cv, file_path, file_path_display, base_name, file_name_without_extension, file_extension, temp_folder, TAB3_etat
    print(TAB3_etat)
    # Réinitialise les variables globales
    initialisation()
    # Ouvre une boîte de dialogue pour choisir un fichier
    file_path = filedialog.askopenfilename()     
    # Vérifie si un fichier a été sélectionné
    if file_path:
        file_path_display = file_path                   # Chemin de l'image à afficher dans l'UI (onglets 1, 2 et 3)
        path, base_name = os.path.split(file_path)   
        file_name_without_extension, file_extension = os.path.splitext(base_name)
  #      print(file_path)
  #      print(base_name)
  #      print(file_name_without_extension)
  #      print(file_extension)
        # Vérifie le type de fichier
        if file_extension in [".jpg", ".jpeg", ".png", ".pdf"]:
            if file_extension == ".pdf":
                file_path_display = convertitPdf(file_path)
                # Sauvegardé dans le dossier factures_temporaire

            image = cv2.imread(file_path_display)

            # Calcule l'angle de l'image pour déterminer s'il faut la redresser
            print("calcul d'angle")
            angle = getSkewAngle(image)
            print(angle)

            # ne redresse pas si l'angle déterminé est soit très petit, soit supérieur à 45 degrés
            if (0.8 < angle < 45) or (-45 < angle < -0.8):
                # Redresse l'image
                image = rotateImage(image, -1 * angle)
                # Sauvegarder dans le dossier factures_temporaire
                file_path_display = temp_folder + '/' + base_name + 'skewed' + '.jpg'
                cv2.imwrite(file_path_display, image)

            #Affiche l'image sélectionnée
            show_image(file_path_display)

            #Charge l'image pour OpenCV (à l'échelle initiale)
            img_cv = cv2.imread(file_path_display)

            #Rend inaccessible l'accès a la TAB 2&3 et Vide les widgets de la TAB3 (#0/1/2/3/4 TAB1=0 ect...)
            deactivate_tab(1) 
            deactivate_tab(2) 
            if TAB3_etat!=0:
                empty_tab(2)
            

        else:
            messagebox.showerror("Erreur", "Type d'image non valide")


# fonction qui convertit un pdf en image (onglet 1)
def convertitPdf(filePath):
    global file_name_without_extension, temp_folder
    # ouvre le fichier pdf
    doc = pymupdf.open(filePath)
    # garde la première page du doc pdf
    page = doc[0]
    # convertit la page 1 en une image
    pix = page.get_pixmap()
    # détermine le chemin du fichier
    new_path = temp_folder + '/' + file_name_without_extension + '.jpg'
    # sauvegarde l'image dans le dossier factures_temporaire
    pix.save(new_path)
    # ferme le document
    doc.close()
    return new_path


# Fonction pour afficher l'image sélectionnée dans le canvas de Tkinter (onglet 1)
def show_image(filePath):
    global photo, min_rescale_factor, w, h, w_r, h_r, max_width_image, max_height_image
    # Ouvre l'image avec PIL
    image = Image.open(filePath)

    # Calcule la taille de l'image et la redimensionne si elle ne rentre pas sur le canvas
    w, h = image.size
    if w > max_width_image or h > max_height_image - 15:      # si l'image est plus grande que le canvas
        # Détermine le facteur de redimentionnement en fonction de la hauteur du canvas (moins une marge
           #  de 15 pour le nom des onglets) et en fonction de la largeur du canvas
        min_rescale_factor = min(max_width_image / w, (max_height_image - 15) / h)
        # Redimensionne l'image pour affichage complet
        resized_image = image.resize((int(w * min_rescale_factor),
                                  int(h * min_rescale_factor)), resample=0)
    else:
        resized_image = image

    w_r, h_r = resized_image.size
    print("largeur image initiale: ", w)
    print("hauteur image initiale: ", h)
    print("largeur image redimensionnée: ", w_r)
    print("hauteur image redimensionnée: ", h_r)
    # Convertit l'image PIL en image Tkinter
    photo = ImageTk.PhotoImage(resized_image)

    # Place l'image au point nord-ouest des canvas de l'onglet 1 et 2
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas2.create_image(0, 0, anchor=tk.NW, image=photo)
        #importation de l'image dans TAB3 se charge uniquement a l'activation de la tab par
    # l'utilisateur si il en a besoin ( économise la mémoire au chargement de l'application. )


# Fonction appelée lors du clic sur le canvas, pour commencer à dessiner un rectangle  (onglet 1)
# associé à l'évènement click de la souris "<ButtonPress-1>" via canvas.bind
def on_canvas_click(event):
    global start_x, start_y, rect_id
    # stocke la position initiale du clic
    start_x, start_y = event.x, event.y
    # récupère l'ID du rectangle & commence à dessiner un rectangle tout petit
    rect_id = canvas.create_rectangle(start_x, start_y, start_x + 1, start_y + 1, outline='red')



# Fonction appelée lors du glissement de la souris avec le bouton pressé,
# pour redimensionner le rectangle (onglet 1)
# associé à l'évènement glissement de la souris "<B1-Motion>" via canvas.bind
def on_canvas_drag(event):
    # position actuelle de la souris
    end_x, end_y = event.x, event.y
    # met à jour les coordonnées du rectangle pour l'agrandir
    canvas.coords(rect_id, start_x, start_y, end_x, end_y)



# Fonction appelée lors du relâchement du bouton de la souris, pour terminer le dessin du
# rectangle   (onglet 1)
# associé à l'évènement relâchement bouton souris "<ButtonRelease-1>" via canvas.bind
def on_canvas_release(event):
    global rect_id, rectangles
    # position finale de la souris
    end_x, end_y = event.x, event.y
    if rect_id:
        # finalise les coordonnées du rectangle
        coordinates = (start_x, start_y, end_x, end_y)
        # ajoute le rectangle à la liste des rectangles du canvas
        rectangles.append([rect_id, coordinates])
        # réinitialise à None l'identifiant du rectangle (pour le prochain)
        rect_id = None



# Fonction pour effacer le dernier rectangle ajouté
def clear_last_rectangle():
    global rectangles
    # vérifie s'il y a des rectangles à effacer
    if rectangles:
        # enlève le dernier rectangle de la liste
        rect_to_delete = rectangles.pop()
        # efface le rectangle du canvas grâce à son ID objet [0] (tuples coords en [1])
        canvas.delete(rect_to_delete[0])


# Fonction pour valider tous les rectangles et extraire le texte des zones correspondantes (onglet 1)
def validate_all():
    global base_name, file_name_without_extension, texte_nettoye, img_cv
    global issuer, date, date_format_dd_mm_yyyy, amount, currency, amount_eur, temp_folder, \
        base_name, file_name_without_extension, min_rescale_factor, rectangles
    global expense_category, id_facture, flag_champs_oblig, w_r, h_r

    # Facteur de mise à l'échelle pour l'agrandissement de l'image et des rectangles
      # permettant une meilleure lecture par Tesseract
    scale_factor = 1.5
    if img_cv is None:
        messagebox.showerror("Erreur", "Aucune image chargée.")
        return

    # Si l'utilisateur n'a pas sélectionné de rectangles, sélectionne toute l'image
    if not rectangles:
        rectangles.append([2, (0, 0, w, h)])

    # Redimensionne l'image
    resized_img = resize_image(img_cv, scale_factor)             # fonction dans module tesseract.py

    print(rectangles)

    # les coordonnées rectangles: ((x1, y1), (x2, y2)) : coin en haut à gauche et coin en bas à droite
    # x[1] = (x2, y2) / x[1][1] = y2 (coord vert. coin en bas à droite) / x[1][0] = x2 (cood
    # horiz. coin en bas à droite)
    # trie d'abord selon y2 plus petit (cad verticalement) et en cas =, selon x2 (horizontalement)
    sorted_rects = sorted(rectangles, key=lambda x: (x[1][1], x[1][0]))

    # Accueille le texte lu par Tesseract
    results = []
    for rect in sorted_rects:
        # Vérifie que les rectangles sélectionnés ne sont pas hors de la facture (coin en haut à gauche x1 et y1)
          # et que les rectangles sont suffisamment grands (x1 != x2 et y1 != y2)
     #   print("Coordonnée du rectangle x1: ", rect[1][0])
     #   print("Coordonnée du rectangle y1: ", rect[1][1])
     #   print("Coordonnée du rectangle x2: ", rect[1][2])
     #   print("Coordonnée du rectangle y2: ", rect[1][3])          
        if rect[1][0] <= w_r and rect[1][1] <= h_r and rect[1][0] != rect[1][2] and rect[1][1] != rect[1][3]: 
            _, coords = rect
            # ajuste les coordonnées des rectangles
            scaled_coords = adjust_and_validate_roi(coords, scale_factor / min_rescale_factor)
            # fonction dans module tesseract.py

            x1, y1, x2, y2 = scaled_coords
            # Extrait la région d'intérêt de l'image redimensionnée
            roi_img = resized_img[y1:y2, x1:x2]

            # Utilise pytesseract pour extraire le texte (--oem : OCR Engine mode; --psm :  mode
            # de segmentation de la page; -l : langue)
            text = pytesseract.image_to_string(roi_img, config='--oem 1 --psm 6 -l fra')    #
            # --psm 6 = présuppose un bloc de texte uniforme

            results.append(text)
        else:
            print("Les rectangles hors de la facture et les rectangles"
                                           " trop petits n'ont pas été traités")    

    full_text = "\n".join(results)

    # Construit le nom du fichier de sortie pour écriture de la traduction dans un fichier
    output_file_name = f"{file_name_without_extension}_text.txt"
    output_path = os.path.join(temp_folder, output_file_name)

    # Ouvre le fichier en écriture
    with open(output_path, 'w') as file:
        # écrit les résultats dans le fichier
        file.write(full_text)

 #   messagebox.showinfo("Extraction terminée", f"Texte enregistré dans {output_path}")

    # Nettoyage du texte
    texte_nettoye = nettoyage_texte_txt(full_text)       # fonction dans module openai_deepl.py

    # Construit le nom du fichier de sortie pour écriture de la traduction dans un fichier
    output_file_name = f"{file_name_without_extension}_nettoye.txt"
    output_path = os.path.join(temp_folder, output_file_name)

    # Ecrit le fichier dans le dossier temporaire
    ecrire_dans_fichier(output_path, texte_nettoye)      # fonction dans module openai_deepl.py

    # Identification automatique des éléments-clés de la facture via le pattern matcher
    issuer = ''  # Emetteur de la facture (à compléter par l'utilisateur)
    issuer_label.set(issuer)

    date_format_dd_mm_yyyy = extract_date(texte_nettoye)   # Date au format string (dd_mm_yyyy)
    # fonction dans module pattern_matcher.py
    date = transf_datestr_obj(date_format_dd_mm_yyyy)   # Date au format objet (yyyy_mm_dd)    #
    # fonction dans module pattern_matcher.py
    date_label.set(date_format_dd_mm_yyyy)

    amount = "{0:.2f}".format(extract_amount(texte_nettoye))   # Montant en devise    # fonction
    # dans module pattern_matcher.py
    print("montant: ", amount)
    amount_label.set(amount)

    currency = extract_currency(texte_nettoye)  # Devise     # fonction dans module
    # pattern_matcher.py
    currency_label.set(currency)

    expense_category = get_categorie(texte_nettoye)[0]      # Catégorie de dépense     # fonction
    # dans module pattern_matcher.py
    expense_category_label.set(expense_category)

    tab_control.tab(1, state='normal')
    switch_to_next_tab()             # Passe à l'onglet 2 pour validation des données par
    # l'utilisateur


# Fonction d'application du pattern matcher et de validation des données principales par
# l'utilisateur (onglet 2)
def validate_main_data():
    global issuer, date, date_format_dd_mm_yyyy, amount, currency, fx_rate, amount_eur, \
        expense_category
    global file_path, chemin_fichier_temp_traduit
    global count
    global expense_category, id_facture, flag_champs_obligatoires, \
        description_champs_obligatoires

    flag_champs_obligatoires = [1, 1, 1, 1, 1]

    # Si l'utilisateur a entré l'émetteur (obligatoire)
    if issuer_entry.get():
        issuer = issuer_entry.get()
    # Si l'émetteur n'est pas renseigné
    elif issuer_label.get() is None or issuer_label.get() == "":
        flag_champs_obligatoires[0] = 0

    # Si l'utilisateur a entré la date de facture
    if date_entry.get():
        date_format_dd_mm_yyyy = date_entry.get()
        # Récupère cette date au format objet (yyyy_mm_dd)
        date = transf_datestr_obj(date_entry.get())   # fonction dans module pattern_matcher.py
    # Si la date de facture n'est pas renseignée
    elif (date_label.get() is None or date_label.get() == "" or date_label.get() == "None"  or
          date_label.get() == " "):
        flag_champs_obligatoires[1] = 0

    # Si l'utilisateur a entré le montant total
    if amount_entry.get():
        amount = amount_entry.get()
    # Si le montant total n'est pas renseigné
    elif amount_label.get() == 0 or amount_label.get() == "":
        flag_champs_obligatoires[2] = 0

    # Si l'utilisateur a entré la devise
    if currency_entry.get():
        currency = currency_entry.get()
        # Si la devise de la facture n'est pas disponible dans le menu déroulant
        if currency == 'Autre':
            messagebox.showinfo("Erreur",
                                "La devise de cette facture n'est pas disponible, "
                                "veuillez contacter l'administrateur")
            flag_champs_obligatoires[3] = 0
    # Si la devise n'est pas renseignée
    elif (currency_label.get() is None or currency_label.get() == "" or currency_label.get()
          not in liste_devises[:-1]):
        flag_champs_obligatoires[3] = 0

    # Si l'utilisateur a entré la catégorie de dépense
    if expense_category_entry.get():
        expense_category = expense_category_entry.get()
    # Si la catégorie de dépense n'est pas renseignée ou inconnue
    elif expense_category_label.get() is None or expense_category_label.get() == "" or \
            expense_category_label.get() == "Inconnu":
        flag_champs_obligatoires[4] = 0

    print("Flags des champs obligatoires: ", flag_champs_obligatoires)

    # Ajout de la facture dans la base de données
    # Si tous les éléments-clé ont été renseignés
    if flag_champs_obligatoires == [1, 1, 1, 1, 1]:
        # Calcule montant facture en EUR si libellée dans une autre devise
        if currency != 'EUR':
            # Maj du nb d'appel de l'API pour les devises (stockée dans var globale "count")
            # Récupère la connexion et le curseur
            connection, cursor = bdd_SQL.connect_to_db()             # fonction dans module
            # bdd_SQL.py
            count=bdd_SQL.compte_conversion_devise_mois(cursor)             # fonction dans
            # module bdd_SQL.py
            if count < 500:
                 # fonction dans module rapidAPI.py:
                amount_eur = "{0:.2f}".format(convertir_devises(amount, currency, 'EUR'))     # A DESACTIVER POUR BLOQUER L'UTILISATION DE L'API DEVISE
                #print(count, "Fonction convertir_devise actuellement désactivée")             # A REACTIVER POUR BLOQUER L'UTILISATION DE L'API DEVISE
                #amount_eur = "{0:.2f}".format(amount)                                         # A REACTIVER POUR BLOQUER L'UTILISATION DE L'API DEVISE
            else:
                messagebox.showinfo("Limite atteinte", "Le nombre de conversions mensuelles"
                                                       " a été atteint.")
                return
        else:
            amount_eur = amount

        amount_eur_confirmed.set(amount_eur)

        # Boîte de dialogue pour validation des données:
        facture_confirmee = messagebox.askokcancel("Confirmation facture",
                                        f"Émetteur: {issuer}\nDate de la facture: {date_format_dd_mm_yyyy}\n"
                                        f"Montant original: {amount} {currency}\nMontant en EUR: {amount_eur} "
                                        f"EUR\nCatégorie: {expense_category}\n\nEnregistrer cette facture?")

        # Si l'utilisateur a validé avec "OK" dans la boîte de dialogue
        if facture_confirmee:
            # Récupère la connexion et le curseur
            connection, cursor = bdd_SQL.connect_to_db()           # fonction dans module bdd_SQL.py
            # Enregistre la nouvelle facture
            id_facture = bdd_SQL.enregistrer_facture(connection, cursor, date, issuer, amount, currency,
                                                     # fonction dans module bdd_SQL.py
                                             amount_eur,
                                             expense_category, 0)
            # Ferme la connexion et le curseur
            bdd_SQL.fermeture_bdd(connection, cursor)           # fonction dans module bdd_SQL.py
            print("Identifiant de la facture entrée dans la base de donnée: ", id_facture)
            messagebox.showinfo("Information", f"L'identifiant attribué à cette facture "
                                      f"est le suivant :{id_facture}")

            # Ecrit le fichier dans le dossier trie
            save_document(file_path, date, amount,           # fonction dans module pattern_matcher.py
                                                expense_category, id_facture)

            # Désactive le bouton de validation des données principales
            button_validate_main_data.config(state="disabled")

            # Active le bouton de demande si traduction souhaitée
            button_view_text.config(state="active")

    # S'il manque des éléments-clé de la facture, émet un message à l'utilisateur
    else:
        amount_eur_confirmed.set(0)
        text_message_box = "\n"
        for i in range(len(flag_champs_obligatoires)):
            if flag_champs_obligatoires[i] == 0:
                text_message_box = text_message_box + description_champs_obligatoires[i] + "\n"
        messagebox.showinfo("Erreur", f"Veuillez entrer les éléments manquants "
                                      f"suivants:{text_message_box}")


# Fonction d'affichage du texte de la facture après que l'utilisateur a confirmé qu'il souhaite une traduction
def want_translation():
    global texte_nettoye
    if texte_nettoye and texte_nettoye != "":
        # Efface le contenu précédent
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, texte_nettoye)
        # Active le bouton de validation du texte
        button_validate_text.config(state="active")


# Fonction de validation du texte par l'utilisateur
def validate_text_for_translation():
    global expense_category, id_facture, date, amount
    global temp_folder, file_name_without_extension, texte_corrige
    texte_corrige = text_widget.get(1.0, tk.END)

    # Construit le nom du fichier de sortie pour écriture de la correction dans un fichier
    output_file_name = f"{file_name_without_extension}_corrige.txt"
    output_path = os.path.join(temp_folder, output_file_name)  # chemin complet du fichier de sortie
    # Ecrit le fichier dans le dossier temporaire
    ecrire_dans_fichier(output_path, texte_corrige)      # fonction dans module openai_deepl.py

    button_validate_text.config(state="disabled")  # Désactive le bouton de validation du texte
    button_view_text.config(state="disabled")  # Désactive le bouton de visualisation du texte
    button_translate.config(state="active")  # Active le bouton de traduction
#   messagebox.showinfo("Information", f"Le fichier corrigé a été sauvegardé")
    

# Fonction de traduction
def translate():
    global file_name_without_extension, id_facture, date, amount, expense_category, \
        language, texte_corrige, chemin_fichier_temp_traduit
    if language_entry.get():
        language = language_entry.get()

        # Traduction du texte et enregistrement des paramètres de traduction dans la base de données
        texte_traduit = traduction_maj_bdd(texte_corrige, language, id_facture)     # fonction dans module openai_deepl.py
        #print(                                                                                      # A REACTIVER POUR BLOQUER L'UTILISATION DE L'API DEEPL + MODIFIER FICHIER openai_deepl
        #    "La fonction traduction_maj_bdd dans openai_deepl doit être remodifiée. "
        #    "Fonctionne actuellement avec fake")

        # Construit le nom du fichier de sortie pour écriture de la traduction dans un fichier
        output_file_name = f"{file_name_without_extension}_translation.txt"
        chemin_fichier_temp_traduit = os.path.join(temp_folder, output_file_name)  # Construit le chemin complet du fichier de sortie

        # Ecrit le fichier dans le dossier temporaire et dans le dossier trie
        ecrire_dans_fichier(chemin_fichier_temp_traduit, texte_traduit)      # Ecriture dans dossier temporaire      # fonction dans module openai_deepl.py
        save_document(chemin_fichier_temp_traduit, date, amount, expense_category, id_facture)   # Ecriture dans dossier trie   # fonction dans module pattern_matcher.py
  #      messagebox.showinfo("Information", f"Le fichier traduit a été sauvegardé")  # Affiche une boîte de dialogue
        return 1
    else:
        # Affiche une boîte de dialogue
        messagebox.showinfo("Erreur", f"Veuillez entrer la langue vers laquelle traduire")
        return 0
        


# Fonction pour activer un onglet spécifique
def activate_tab(idx):
    tab_control.tab(idx, state='normal')  #0/1/2/3/4 TAB1=0 ect...
    print("Onglet activé : ", idx+1)


# Fonction pour désactiver un onglet spécifique au démarrage
def deactivate_tab(tab):
    # Désactive l'onglet au démarrage
    tab_control.tab(tab, state='disabled') #0/1/2/3/4 TAB1=0 ect...
    print("Onglet désactivé: ", tab+1)

# Lance l'onglet de traduction
def translate_activate():
    if translate() == 1: # Lance la traduction
        activate_tab(2) # Donne accès a l'utilisateur a la TAB3
        setup_tab3(chemin_fichier_temp_traduit) # Charge la TAB3 si l'utilisateur en a vraiment besoin
        switch_to_next_tab() # Emmène l'utilisateur directement a la TAB 3

# Sert a vider tout les widgets de la TAB (#0/1/2/3/4 TAB1=0 ect...)
def empty_tab(tab):
    global TAB3_etat
    TAB3_etat=0 #Reset l'état de la fenêtre pour éviter l'appel d'une fonction vidant la tab3
    # a chaque clique sur le bouton import image.
    print("Suppression des widgets de la TAB3")
    for widget in tab.winfo_children(): # Récupère tout les widgets de la TAB selectionné
        widget.destroy()    # Détruit les widgets

#Fonction utile pour la TAB3
def save_text():
    global text_widget2, file_name_without_extension, temp_folder
    """sauvegarde le contenu de la zone de texte dans un fichier."""

    # Construit le nom du fichier de sortie pour écriture de la correction de la traduction dans un fichier
    output_file_name = f"{file_name_without_extension}_translation.txt"
    output_path = os.path.join(temp_folder, output_file_name)  # Construit le chemin complet du fichier de sortie

    texte_traduit_confirme = text_widget2.get("1.0", tk.END)

    # Ecrit le fichier dans le dossier temporaire et dans le dossier trie
    ecrire_dans_fichier(output_path, texte_traduit_confirme)      # fonction dans module openai_deepl.py
    save_document(output_path, date, amount, expense_category, id_facture)         # fonction dans module pattern_matcher.py

    # Affichage de la confirmation de sauvegarde
    messagebox.showinfo("Information", f"Le texte a été sauvegardé avec succès")

# ***********************************************************************************************************************************

# *** FONCTIONS LIÉES AUX ONGLETS 4 ET 5 (COMPTABILITÉ ET STATISTIQUES) *****

# Initialise les variables globales et nettoie l'onglet comptabilité (parties de gauche et du milieu, qui dépendent d'une période entrée par l'utilisateur)
def initialisation_acc():
    global accounting_month, accounting_year, previous_accounting_year, somme_montant_cat_year_n, \
        somme_montant_cat_year_n_1
    # Mois de référence pour onglet comptabilité
    accounting_month = None
    # Année de référence pour onglet comptabilité
    accounting_year = 0
    previous_accounting_year = 0

    # Efface le contenu des champs de l'UI:
    expense_category_entry_acc.delete(0, "end")
    text_widget_acc.delete(1.0, tk.END)

    # Active / désactive les boutons:
    button_category_detail.config(state="disabled")
        # Désactive le bouton pour obtenir le détail d'une catégorie de dépenses

# Initialise les variables globales et nettoie l'onglet comptabilité complètement
def initialisation_acc_full():
    global length_expense_category

    # Efface le contenu des champs de l'UI et réinitialise les variables globales partie comptabilité sur une période:
    accounting_month_entry.delete(0, "end")         # remet à zéro le menu déroulant
    accounting_year_entry.delete(0, "end")         # remet à zéro le menu déroulant

    label_month_var.set("")                     # efface le contenu des étiquettes mois et année
    label_year_n_var.set("")
    label_year_n_1_var.set("")

    for i in range(length_expense_category):        # remet les montants à zéro
        somme_montant_cat_year_n[i].set(0) 
        somme_montant_cat_year_n_1[i].set(0)
    total_year_n.set(0)
    total_year_n_1.set(0)

    initialisation_acc()                        # remet à zéro le reste des informations

    # Efface le contenu des champs de l'UI partie facture individuelle:
    invoice_id_acc.delete(0, "end")
    text_widget_details_facture.delete(1.0, tk.END)


# Fonction de comptabilité (visualisation des montants par catégorie pour une période donnée)
def display_sums():
    global accounting_month, accounting_year, categorie, padding_x_first_r, padding_x_acc, length_expense_category, \
        somme_montant_cat_year_n, somme_montant_cat_year_n_1
    initialisation_acc()

    if accounting_month_entry.get() and accounting_month_entry.get() != 'tous':
        accounting_month = accounting_month_entry.get()
        label_month_var.set(accounting_month)
    else:
        accounting_month = None
        label_month_var.set("")

    if accounting_year_entry.get():
        accounting_year = int(accounting_year_entry.get())
        previous_accounting_year = accounting_year - 1
        label_year_n_var.set(accounting_year)
        label_year_n_1_var.set(previous_accounting_year)
        total_categories_n = 0
        total_categories_n_1 = 0

        button_category_detail.config(state="active")
        # Active le bouton permettant de voir les détails d'une catégorie de dépenses

        # Récupère la connexion et le curseur
        connection, cursor = bdd_SQL.connect_to_db()

        # Pour chaque catégorie de dépense:
        for i in range(length_expense_category):
            # Définit la catégorie que l'on va rechercher
            categorie = liste_categorie_depense[i]
            # Stocke le résultat pour une catégorie dans une variable (année n et n-1)
            somme_montant_cat_year = bdd_SQL.somme_factures_categorie(accounting_month, accounting_year, categorie, cursor)
            somme_montant_cat_prev_year = bdd_SQL.somme_factures_categorie(accounting_month, previous_accounting_year,
                                                                   categorie, cursor)

            # Vérifie que le montant total est un float (car montant est de type FLOAT) non négatif
            assert isinstance(somme_montant_cat_year, float) and somme_montant_cat_year >= 0.0, \
                "Le montant total par catégorie doit être un flottant non négatif"
            assert isinstance(somme_montant_cat_prev_year, float) and somme_montant_cat_prev_year >= 0.0, \
                "Le montant total par catégorie doit être un flottant non négatif"

            # Met à jour l'onglet 4
            somme_montant_cat_year_n[i].set("{0:,.2f}".format(somme_montant_cat_year))
            somme_montant_cat_year_n_1[i].set("{0:,.2f}".format(somme_montant_cat_prev_year))
            total_categories_n += somme_montant_cat_year
            total_categories_n_1 += somme_montant_cat_prev_year

        # Somme des catégories
        total_year_n.set(f"{total_categories_n:10,.2f}")
        total_year_n_1.set(f"{total_categories_n_1:10,.2f}")

        # Ferme la connexion et le curseur
        fermeture_bdd(connection, cursor)
    else:
        messagebox.showinfo("Erreur", f"Veuillez entrer l'année")
        # Affiche une boîte de dialogue


def display_list_invoice():
    global accounting_month, accounting_year

    if expense_category_entry_acc.get():  # si l'utilisateur a entré la catégorie de dépense
        expense_category_detail = expense_category_entry_acc.get()

        # Récupère la connexion et le curseur
        connection, cursor = bdd_SQL.connect_to_db()

        # Imprime le détail des factures pour la catégorie
        details_category = bdd_SQL.details_factures_categorie(expense_category_detail,
                                                      accounting_month, accounting_year,
                                                      cursor)
        text_widget_acc.delete(1.0, tk.END)
        # Efface le contenu de la fenêtre de texte
        text_widget_acc.insert(tk.END, details_category)
        # Insère les détails de la facture dans la fenêtre de texte

        # Ferme la connexion et le curseur
        bdd_SQL.fermeture_bdd(connection, cursor)
    else:
        messagebox.showinfo("Erreur",
                            f"Veuillez entrer une catégorie de dépense")

def display_details_invoice():
    if invoice_id_acc.get():  # Si l'utilisateur a entré l'identifiant de la facture
        id_facture_acc = invoice_id_acc.get()

        # Récupère la connexion et le curseur
        connection, cursor = bdd_SQL.connect_to_db()

        # Imprime le détail des factures pour la catégorie
        details_invoice = bdd_SQL.afficher_informations_facture(cursor, id_facture_acc)
        text_widget_details_facture.delete(1.0, tk.END)
        # Efface le contenu de la fenêtre de texte
        text_widget_details_facture.insert(tk.END, details_invoice)
        # Insère les détails de la facture dans la
        # Fenêtre de texte

        # Ferme la connexion et le curseur
        bdd_SQL.fermeture_bdd(connection, cursor)
    else:
        messagebox.showinfo("Erreur",
                            f"Veuillez entrer l'identifiant de la facture")
def display_invoice():
    global month_names, sort_folder, width_ui, height_ui, max_width_image, max_height_image
    if invoice_id_acc.get() and invoice_id_acc.get() != 0:
        # Si l'utilisateur a entré l'identifiant de la facture
        id_facture_acc = invoice_id_acc.get()

        # Récupère la connexion et le curseur
        connection, cursor = bdd_SQL.connect_to_db()
        # Récupère les informations catégorie et dates de la facture
        try:
            category_invoice = bdd_SQL.afficher_categorie_facture(cursor, id_facture_acc)
            if category_invoice == "Aucune facture trouvée avec cet ID." :
                print(f"La facture {id_facture_acc} n'a pas été trouvée dans la base de données") 
                messagebox.showinfo("Erreur", f"La facture {id_facture_acc} n'a pas été trouvée dans la base de données")
                return

        except:
            print(f"La facture {id_facture_acc} n'a pas été trouvée dans la base de données") 
            messagebox.showinfo("Erreur", f"La facture {id_facture_acc} n'a pas été trouvée dans la base de données")
            return
        
        date_invoice = bdd_SQL.afficher_date_facture(cursor, id_facture_acc)
        year_invoice = str(date_invoice.year)
        # Utilisation du dictionnaire pour le nom du mois
        month_invoice = month_names[date_invoice.strftime('%m')]
        # Ferme la connexion et le curseur
        bdd_SQL.fermeture_bdd(connection, cursor)

        # Localise la facture dans les factures triées
        found_invoice_flag = 0
        path_trie = sort_folder + "/" + year_invoice + "/" + month_invoice + "/" + category_invoice + "/"
        file_path_trie_indiv = None
        for roots, dirs, files in os.walk(path_trie):
            # Pour chaque fichier scanné:
            for name in files: 
                if name.split('_')[0] == id_facture_acc and name.split('.')[-1] != 'txt':       # S'il ne s'agit pas d'un fichier texte
                    file_path_trie_indiv = os.path.join(path_trie, name)                        # Récupère le chemin complet du fichier
                    if name.split('.')[-1] == 'pdf':                                            # S'il s'agit d'un pdf
                        file_path_trie_indiv = convertitPdf(file_path_trie_indiv)               # Convertit en image (sauvegardé dans factures temporaires) pour chargement dans UI
                    found_invoice_flag = 1

        # Si la facture est trouvée, ouvre une nouvelle fenêtre dans l'UI pour l'afficher
        if found_invoice_flag == 1:  # Si la facture a été trouvée
            tab_display_invoice = tk.Toplevel(root)  # Ouvre une nouvelle fenêtre
            size_ui = str(width_ui) + 'x' + str(height_ui)
            tab_display_invoice.geometry(size_ui)  # Dimension de la fenêtre
            tab_display_invoice.title("Facture")  # Titre de la fenêtre

            try:
                image_detail = Image.open(file_path_trie_indiv)  # Ouvre l'image avec PIL
                w_detail_inv, h_detail_inv = image_detail.size
                min_rescale_factor_detail_inv = min(max_width_image         # Détermine la taille maximum de l'image pour affichage
                                                    / w_detail_inv, max_height_image / h_detail_inv)
                resized_image_detail_inv = image_detail.resize((int(w_detail_inv *
                                                                    min_rescale_factor_detail_inv),
                                                                int(h_detail_inv * min_rescale_factor_detail_inv)),
                                                               resample=0)
                # Redimensionne l'image pour affichage complet
                photo_detail_inv = ImageTk.PhotoImage(
                    resized_image_detail_inv)  # convertit l'image PIL en image Tkinter
                panel_invoice = tk.Label(tab_display_invoice, image=photo_detail_inv)
                panel_invoice.image = photo_detail_inv
                panel_invoice.pack()

            # Gestion des erreurs
            except FileNotFoundError:
                print(f"Le fichier {file_path_trie_indiv} n'a pas été trouvé.")
                messagebox.showinfo("Erreur", f"Le fichier n'a pas été trouvé")
            except Exception as e:
                print(f"Une erreur est survenue lors de la lecture du fichier: {e}")
                messagebox.showinfo("Erreur", f"Une erreur est survenue lors "
                                              f"de la lecture du fichier")
        else:
            messagebox.showinfo("Erreur", f"La facture n'a pas été trouvée")
    else:
        messagebox.showinfo("Erreur",
                            f"Veuillez entrer l'identifiant de la facture")


def display_invoice_translation():
    global month_names, sort_folder, width_ui, height_ui
    if invoice_id_acc.get() and invoice_id_acc.get() != 0:
        # Si l'utilisateur a entré l'identifiant de la facture
        id_facture_acc = invoice_id_acc.get()

        # Récupère la connexion et le curseur
        connection, cursor = connect_to_db()
        # Récupère les informations catégorie et dates de la facture
        try:
            category_invoice = afficher_categorie_facture(cursor, id_facture_acc)
            if category_invoice == "Aucune facture trouvée avec cet ID." :
                print(f"La facture {id_facture_acc} n'a pas été trouvée dans la base de données") 
                messagebox.showinfo("Erreur", f"La facture {id_facture_acc} n'a pas été trouvée dans la base de données")
                return
        except:
            print(f"La facture {id_facture_acc} n'a pas été trouvée dans la base de données") 
            messagebox.showinfo("Erreur", f"La facture {id_facture_acc} n'a pas été trouvée dans la base de données")
            return
        
        date_invoice = afficher_date_facture(cursor, id_facture_acc)
        year_invoice = str(date_invoice.year)
        # Utilisation du dictionnaire pour le nom du mois
        month_invoice = month_names[date_invoice.strftime('%m')]
        # Ferme la connexion et le curseur
        fermeture_bdd(connection, cursor)

        # Localise la traduction de la facture dans les factures triées
        found_invoice_translation_flag = 0
        path_trie = (sort_folder + "/" + year_invoice + "/" +
                     month_invoice + "/" + category_invoice + "/")
        file_path_trie_indiv = None
        for roots, dirs, files in os.walk(path_trie):
            for name in files:
                if name.split('_')[0] == id_facture_acc and name.split('.')[-1] == 'txt':
                    file_path_trie_indiv = os.path.join(path_trie, name)
                    found_invoice_translation_flag = 1

        # Si la traduction a été localisée, , ouvre une nouvelle fenêtre dans l'UI pour l'afficher
        if found_invoice_translation_flag == 1:
            # Ouvre une nouvelle fenêtre
            tab_display_invoice_translation = tk.Toplevel(root)
            size_ui = str(width_ui) + 'x' + str(height_ui)
            # Dimension de la fenêtre
            tab_display_invoice_translation.geometry(size_ui)
            # Titre de la fenêtre
            tab_display_invoice_translation.title("Traduction de la facture")
            # Information sur le numéro de la facture traduite
            (label_facture_traduction := tk.Label(tab_display_invoice_translation,
                                                  text="Traduction de la facture no")
             ).grid(row=1, column=1, padx=(450, 0), pady=10)
            id_facture_invoice_translation = tk.DoubleVar(value=id_facture_acc)
            (tk.Label(tab_display_invoice_translation, textvariable=id_facture_invoice_translation)
             .grid(row=1, column=2, padx=0, pady=10))
            # Widget de texte pour afficher la traduction
            text_widget_invoice_tranlation = tk.Text(tab_display_invoice_translation, wrap="word",
                                                     width=70, height=55)
            text_widget_invoice_tranlation.grid(row=2, column=1, columnspan=2, padx=(450, 0), pady=10)
            font = tkFont.Font(font=label_facture_traduction['font']).actual()
            text_widget_invoice_tranlation.configure(font=(font['family'], font['size']))

            try:
                # On extrait le texte du fichier
                with open(file_path_trie_indiv, 'r', encoding='utf-8') as fichier:
                    texte_invoice_translation = fichier.read()
                    text_widget_invoice_tranlation.insert(tk.END, texte_invoice_translation)
            # Gestion des erreurs
            except FileNotFoundError:
                print(f"Le fichier {file_path_trie_indiv} n'a pas été trouvé.")
                messagebox.showinfo("Erreur", f"Le fichier n'a pas été trouvé")
            except Exception as e:
                print(f"Une erreur est survenue lors de la lecture du fichier: {e}")
                messagebox.showinfo("Erreur", f"Une erreur est survenue lors de "
                                              f"la lecture du fichier")
        else:
            messagebox.showinfo("Erreur", f"La traduction de la facture n'a pas été trouvée")
    else:
        messagebox.showinfo("Erreur",
                            f"Veuillez entrer l'identifiant de la facture")


def delete_invoice():
    global month_names, sort_folder
    if invoice_id_acc.get() and invoice_id_acc.get() != 0:
        # Si l'utilisateur a entré l'identifiant de la facture
        id_facture_acc = invoice_id_acc.get()

        # Récupère la connexion et le curseur
        connection, cursor = bdd_SQL.connect_to_db()
        # Récupère les informations catégorie et dates de la facture
        category_invoice = bdd_SQL.afficher_categorie_facture(cursor, id_facture_acc)
        if category_invoice == "Aucune facture trouvée avec cet ID." :
            print(f"La facture {id_facture_acc} n'a pas été trouvée dans la base de données") 
            messagebox.showinfo("Erreur", f"La facture {id_facture_acc} n'a pas été trouvée dans la base de données")
            return
        date_invoice = bdd_SQL.afficher_date_facture(cursor, id_facture_acc)
        year_invoice = str(date_invoice.year)

        # Boîte de dialogue pour validation des données:
        effacer_facture = messagebox.askokcancel("Confirmation suppression de facture",
                                        f"Êtes-vous sûr de vouloir supprimer la facture {id_facture_acc} ainsi que sa traduction de la base de données et des fichiers trie ? \n\n")

        if effacer_facture == True:

            # Supprime la facture de la base de données:
            try:
                bdd_SQL.supprimer_facture(id_facture_acc, cursor, connection)    
            except :
                print(f"La facture {id_facture_acc} n'a pas pu être supprimée de la base de données") 
                messagebox.showinfo("Erreur", f"La facture {id_facture_acc} n'a pas pu être supprimée de la base de données")

            # Utilisation du dictionnaire pour le nom du mois
            month_invoice = month_names[date_invoice.strftime('%m')]
            # ferme la connexion et le curseur
            bdd_SQL.fermeture_bdd(connection, cursor)

            # Localise la traduction de la facture dans les factures triées
            found_invoice_translation_flag = 0
            path_trie = (sort_folder + "/" + year_invoice + "/" +
                     month_invoice + "/" + category_invoice + "/")

            # Trouve la facture dans le dossier trie pour la supprimer
            file_path_trie_indiv = None

            for roots, dirs, files in os.walk(path_trie):
                for name in files:
                    if name.split('_')[0] == id_facture_acc and name.split('.')[-1] != 'txt':
                        file_path_trie_indiv = os.path.join(path_trie, name)
                        found_invoice_flag = 1

            # Si la facture a été trouvée
            if found_invoice_flag == 1:
                try:
                    # Efface le fichier
                    os.remove(file_path_trie_indiv)

                # Gestion des erreurs
                except FileNotFoundError:
                    print(f"Le fichier {file_path_trie_indiv} n'a pas été trouvé.")
                    messagebox.showinfo("Erreur", f"Le fichier n'a pas été trouvé")
                except Exception as e:
                    print(f"Une erreur est survenue lors de la lecture du fichier: {e}")
                    messagebox.showinfo("Erreur", f"Une erreur est survenue lors de "
                                              f"la lecture du fichier")
            else:
                messagebox.showinfo("Erreur", f"La facture n'a pas été trouvée dans le dossier trie")

            # Trouve le fichier traduction de la facture dans le dossier trie pour le supprimer
            file_path_trie_indiv = None
            for roots, dirs, files in os.walk(path_trie):
                for name in files:
                    if name.split('_')[0] == id_facture_acc and name.split('.')[-1] == 'txt':
                        file_path_trie_indiv = os.path.join(path_trie, name)
                        found_invoice_translation_flag = 1

            # Si le fichier de traduction a été trouvé
            if found_invoice_translation_flag == 1:
                try:
                    # Efface le fichier
                    os.remove(file_path_trie_indiv)

                # Gestion des erreurs
                except FileNotFoundError:
                    print(f"Le fichier {file_path_trie_indiv} n'a pas été trouvé.")
                    messagebox.showinfo("Erreur", f"Le fichier n'a pas été trouvé")
                except Exception as e:
                    print(f"Une erreur est survenue lors de la lecture du fichier: {e}")
                    messagebox.showinfo("Erreur", f"Une erreur est survenue lors de "
                                              f"la lecture du fichier")
            else:
                messagebox.showinfo("Erreur", f"La traduction de la facture n'a pas été trouvée dans le dossier trie")

    else:
        messagebox.showinfo("Erreur",
                            f"Veuillez entrer l'identifiant de la facture")

# Chargement de la table à chaque clic sur l'onglet, afin d'actualiser l'information affichée dans l'onglet.
def tab_selected(event):
    # Récupère le nom de l'onglet sélectionné
    selected_tab = event.widget.tab(event.widget.index("current"), "text")
    if selected_tab == "Statistiques":
        # Détruit tous les widgets dans l'onglet 5 pour éviter les duplications
        for widget in tab5.winfo_children():
            widget.destroy()
        # Reconfigure l'onglet 5 avec les widgets mis à jour
        setup_tab5()


# Met à jour les résultats en fonction de la catégorie, du mois et de l'année sélectionnés
def update_result(category, selected_month, selected_year, result_label, selected_category=None):
    global Var_stockage_cate
    #print(Var_stockage_cate) # Print utilisé pour le développement afin de vérifier la catégorie sélectionnée

    # Vérifie si une année valide est sélectionnée, sinon affiche un message d'erreur
    if selected_year == "Choisir une année":
        result_label.config(text="Veuillez sélectionner une année valide.")
        return

    # Établit une connexion à la base de données
    connection, cursor = connect_to_db()
    if connection is None or cursor is None:
        # Affiche un message d'erreur si la connexion à la base de données échoue
        result_label.config(text="Échec de la connexion à la base de données.")
        return

    # Vérifie si une catégorie spécifique est sélectionnée et la stocke dans une variable globale
    if selected_category is not None:
        Var_stockage_cate = selected_category
    else:
        selected_category = Var_stockage_cate

    # Détermine le mois et l'année à utiliser dans la requête
    mois = None if selected_month == "Choisir un mois" else selected_month
    annee = selected_year

    # Mappe chaque catégorie à une fonction SQL correspondante
    function_map = {
        "Nombre de factures :": lambda: bdd_SQL.nb_facture_traitees(mois, annee, cursor),
        "Catégorie la plus fréquente :": lambda: bdd_SQL.categorie_plus_frequente(mois, annee, cursor),
        "Nombre de factures traduites (selon date d'émission) :": lambda:
        bdd_SQL.nb_factures_traduites(mois,
                                                                                        annee, cursor),
        "Langues de traduction les plus fréquentes :": lambda: bdd_SQL.frequence_toutes_langues_cibles(mois, annee,cursor),
        "Nombre de caractères traduits (API) :": lambda: bdd_SQL.nb_caracteres_traduits(mois, annee, cursor),
        "Prix moyen des factures :": lambda: str(bdd_SQL.prix_moyen_facture(mois, annee, cursor)) + " €",
        "Prix moyen d'une facture d'une catégorie précise :": lambda: str(bdd_SQL.prix_moyen_facture_categorie(mois, annee, selected_category, cursor)) + " €",
    }

    # Exécute la fonction correspondante à la catégorie sélectionnée et met à jour le label des résultats
    if category in function_map:
        try:
            result = function_map[category]()
            result_label.config(text=str(result))
        except Exception as e:
            result_label.config(text=f"Erreur : {e}")
    else:
        result_label.config(text="Fonction non définie pour cette catégorie.")


# Fonction appelée lorsque la sélection de l'année change
def year_selection_changed(event, year_cb, month_cb, category, result_label):
    #Ajuste l'état de la combobox mois et met à jour les résultats en fonction de l'année sélectionnée.
    selected_year = year_cb.get()
    # Réinitialise la sélection du mois à "Choisir un mois" chaque fois que la sélection de l'année change
    month_cb.set("Choisir un mois")

    if selected_year == "Depuis toujours":
        # Désactive le combobox des mois si "Depuis toujours" est sélectionné
        month_cb.config(state="disabled")
        # Met à jour le résultat pour toutes les années
        update_result(category, None, "toutes", result_label)
    else:
        # Active le combobox des mois
        month_cb.config(state="readonly")
        # Met à jour le résultat en fonction de l'année sélectionnée
        update_result(category, None, selected_year, result_label)
        


# Fonction appelée lorsque la sélection du mois change
def month_selection_changed(event, year_cb, month_cb, category, result_label):
    # Récupère l'année et le mois sélectionnés
    selected_year = year_cb.get()
    selected_month = month_cb.get()
    # Vérifie si l'année est sélectionnée avant de mettre à jour les résultats
    if selected_year == "Choisir une année":
        result_label.config(text="Veuillez sélectionner une année.")
        return
    # Met à jour le résultat en fonction du mois et de l'année sélectionnés
    update_result(category, selected_month, selected_year, result_label)

# ***********************************************************************************************************************************

def style_configure():
    style = ttk.Style()
    style.theme_use('clam')  # Basé sur un thème existant pour faciliter la personnalisation

    # Configuration générale du thème sombre
    style.configure("TFrame", background="#333333") #pour TFrame style fonctionne
    style.configure("TLabel", background="#333333", foreground="#ffffff", font=('Helvetica', 12, 'bold')) #pour TLabel style fonctionne 
    style.configure("TButton", background="#555555", foreground="#ffffff", font=('Helvetica', 10, 'bold'), borderwidth=1)  # Boutons en mode sombre fonctionne
    style.configure("TEntry", background="#555555", foreground="#ffffff", fieldbackground="#555555") # Boutons en mode sombre Fonctionne
    style.configure("Light.TCombobox", fieldbackground="#555555", background="#555555", foreground="white", arrowcolor="white") # Boutons combobox en mode sombre fonctionne
    style.map('Light.TCombobox', fieldbackground=[('readonly', '#555555')], selectbackground=[('readonly', '#555555')], selectforeground=[('readonly', 'white')]) # Boutons combobox en mode sombre fonctionne
    style.configure('Custom.TNotebook', background='#333333') # Configuration du stye du notebook ( derrière les onglets )
    
# ************************ CREATION DE L'UI  ************************

# Création de l'interface graphique principale
root = tk.Tk()
size_ui = str(width_ui) + 'x' + str(height_ui)
root.geometry(size_ui)  # Dimension de la fenêtre
root.title("ProjectL2")  # Titre de la fenêtre

tab_control = ttk.Notebook(root, style='Custom.TNotebook')

# Création des 5 onglets de l'UI
tab1 = ttk.Frame(tab_control)
tab2 = ttk.Frame(tab_control)
tab3 = ttk.Frame(tab_control)
tab4 = ttk.Frame(tab_control)
tab5 = ttk.Frame(tab_control)
tab_control.add(tab1, text="Affichage Image")
tab_control.add(tab2, text="Vérification", state='disabled')
tab_control.add(tab3, text="Traduction")
tab_control.add(tab4, text="Comptabilité")
tab_control.add(tab5, text="Statistiques")


# Fonction pour passer à l'onglet suivant
def switch_to_next_tab():
    current_tab_index = tab_control.index("current")
    next_tab_index = (current_tab_index + 1) % tab_control.index("end")
    tab_control.select(next_tab_index)


# Créer l'onglet "Affichage Image" (Onglet 1)
canvas = tk.Canvas(tab1, bg="#333333")  # Crée un canvas pour dessiner et afficher l'image
canvas.grid(row=0, column=0, sticky="nsew")

right_frame = tk.Frame(tab1, bg="#333333")
right_frame.grid(row=0, column=1, sticky="new")

tab1.columnconfigure(0, weight=5)  # Répartit les colonnes avec un ration de 5 contre 1
tab1.columnconfigure(1, weight=1)

# Bouton pour obtenir le manuel d'utilisation
(tk.Button(right_frame, text="Manuel d'utilisation", command=manuel_utilisation_tab_1).
    grid(row=1, column=0,padx=(150, 10), pady=(20, 10)))

# Bouton pour importer une image
tk.Button(right_frame, text="Importer Image", command=import_image).grid(row=2, column=0, padx=(150, 10),
                                                                         pady=(150, 10))

# Associe l'événement de clic à la fonction on_canvas_click
canvas.bind("<ButtonPress-1>", on_canvas_click)
# Associe le glissement de la souris avec bouton pressé à la fonction on_canvas_drag
canvas.bind("<B1-Motion>", on_canvas_drag)
# Associe le relâchement du bouton à la fonction on_canvas_release
canvas.bind("<ButtonRelease-1>", on_canvas_release)

# Bouton pour effacer le dernier rectangle
tk.Button(right_frame, text="Effacer Dernier Rectangle",
          command=clear_last_rectangle).grid(row=3, column=0,padx=(150, 10),pady=(50, 10))

# Bouton pour valider l'extraction du texte
tk.Button(right_frame, text="Valider Tout", command=validate_all).grid(row=4, column=0,
                                                                       padx=(150, 10), pady=(490, 10))


# Créer l'onglet "Vérification" (Onglet 2)
canvas2 = tk.Canvas(tab2, bg="#333333")  # Crée un canvas pour dessiner et afficher l'image
canvas2.grid(row=0, column=0, sticky="nsew")

right_frame2 = tk.Frame(tab2, bg="#333333")
right_frame2.grid(row=0, column=1, sticky="nse")

tab2.columnconfigure(0, weight=3)  # Répartit les colonnes
tab2.columnconfigure(1, weight=1)

# Colonnes "proposé" et "corrigé"
(label_propose := tk.Label(right_frame2, text="Proposé",background="#333333", foreground="white",)).grid(row=0,
                                                    column=1, padx=padding_x_1, pady=padding_y_fin)
font = tkFont.Font(font=label_propose['font']).actual()
label_propose.configure(font=(font['family'], font['size'], 'bold'))
(label_corrige := tk.Label(right_frame2, text="Corrigé",background="#333333", foreground="white",)).grid(row=0,
                                                    column=2, padx=padding_x_2, pady=padding_y_fin)
font = tkFont.Font(font=label_corrige['font']).actual()
label_corrige.configure(font=(font['family'], font['size'], 'bold'))

# Emetteur de la facture:
tk.Label(right_frame2, text="Émetteur de la facture:",background="#333333", foreground="white",).grid(row=1,
                                                column=0, padx=padding_x_0, pady=padding_y_fin)
issuer_label = tk.StringVar(value=None)
tk.Label(right_frame2, textvariable=issuer_label,background="#333333", foreground="white").grid(row=1,
                                                column=1, padx=padding_x_1, pady=padding_y_fin)
(issuer_entry := tk.Entry(right_frame2, background="#555555", foreground="white")).grid(row=1,
                                              column=2, padx=padding_x_2, pady=padding_y_fin)

# Date de la facture:
tk.Label(right_frame2, text="Date de la facture:",background="#333333", foreground="white",).grid(row=2,
                                                column=0, padx=padding_x_0, pady=padding_y_fin)
date_label = tk.StringVar(value=None)
tk.Label(right_frame2, textvariable=date_label,background="#333333", foreground="white").grid(row=2,
                                            column=1, padx=padding_x_1, pady=padding_y_fin)
date_entry = DateEntry(right_frame2, date_pattern="dd-mm-yyyy", style="Light.TCombobox")
date_entry.delete(0, "end")
date_entry.grid(row=2, column=2, padx=padding_x_2, pady=padding_y_fin)

# Montant et devise de la facture:
tk.Label(right_frame2, text="Montant:",background="#333333", foreground="white",).grid(row=3,
                                    column=0, padx=padding_x_0, pady=padding_y)
amount_label = tk.DoubleVar(value=0)
tk.Label(right_frame2, textvariable=amount_label,background="#333333", foreground="white").grid(row=3,
                                        column=1, padx=padding_x_1, pady=padding_y)
(amount_entry := tk.Entry(right_frame2, background="#555555", foreground="white")).grid(row=3,
                                    column=2, padx=padding_x_2, pady=padding_y)

tk.Label(right_frame2, text="Devise:",background="#333333", foreground="white",).grid(row=4,
                                column=0, padx=padding_x_0, pady=padding_y)
currency_label = tk.StringVar(value=None)
tk.Label(right_frame2, textvariable=currency_label,background="#333333", foreground="white").grid(row=4,
                                            column=1, padx=padding_x_1, pady=padding_y)
(currency_entry := ttk.Combobox(right_frame2, values=liste_devises, style="Light.TCombobox")).grid(row=4,
                                                column=2, padx=padding_x_2,pady=padding_y)

# Affichage du montant en euros, pour information:
tk.Label(right_frame2, text="Montant en EUR:",background="#333333", foreground="white",).grid(row=5, column=0,
                                                    padx=padding_x_0, pady=padding_y_fin)
amount_eur_confirmed = tk.DoubleVar(value=0)
tk.Label(right_frame2, textvariable=amount_eur_confirmed,background="#333333", foreground="white").grid(row=5, column=2,
                                                               padx=padding_x_2, pady=padding_y_fin)

# Catégorie de dépense:
tk.Label(right_frame2, text="Catégorie de dépense:",background="#333333", foreground="white",).grid(row=6, column=0,
                                                          padx=padding_x_0, pady=padding_y)
expense_category_label = tk.StringVar(value=None)
tk.Label(right_frame2, textvariable=expense_category_label,background="#333333", foreground="white").grid(row=6,
                                                                 column=1, padx=padding_x_1, pady=padding_y)
((expense_category_entry := ttk.Combobox(right_frame2, values=liste_categorie_depense, style="Light.TCombobox")).grid(
            row=6, column=2, padx=padding_x_2, pady=padding_y))

# Bouton de validation des données clés de la facture:
button_validate_main_data = tk.Button(right_frame2, text="Valider données", command=validate_main_data)
button_validate_main_data.grid(row=8, column=1, padx=padding_x_1, pady=padding_y_fin)

# Affichage du texte et bouton de validation du texte:
button_view_text = tk.Button(right_frame2, text="Afficher le texte pour traduction", command=want_translation)
button_view_text.grid(row=13, column=1, padx=padding_x_1, pady=padding_y)
button_view_text.config(state="disabled")  # Désactive le bouton de visualisation du texte

text_widget = tk.Text(right_frame2, wrap="word", width=80, height=25)
text_widget.grid(row=14, column=0, columnspan=3, padx=(10, 20), pady=padding_y)
text_widget.configure(font=(font['family'], font['size']))

button_validate_text = tk.Button(right_frame2, text="Valider texte", command=validate_text_for_translation)
button_validate_text.grid(row=15, column=1, padx=padding_x_1, pady=padding_y_fin)
button_validate_text.config(state="disabled")  # désactive le bouton de validation du texte


# Modification du bouton traduire pour faire en sorte d'activer le bouton à la sélection de la langue
def language_select(event):
    # Active le bouton lorsque une langue est sélectionnée
    button_translate.config(state="normal")


# Traduction et bouton de validation pour lancer la traduction:
label_langues = tk.Label(right_frame2, text="Traduire en:",background="#333333", foreground="white")
label_langues.grid(row=16, column=0, padx=padding_x_0, pady=padding_y)

liste_langues = ('anglais', 'espagnol', 'allemand')
language_entry = ttk.Combobox(right_frame2, values=liste_langues, style="Light.TCombobox")
language_entry.grid(row=16, column=1, padx=padding_x_1, pady=padding_y)
language_entry.bind("<<ComboboxSelected>>", language_select)

button_translate = tk.Button(right_frame2, text="Traduire", command=translate_activate)
button_translate.grid(row=17, column=1, padx=padding_x_1, pady=padding_y_fin)
button_translate.config(state="disabled")  # Désactive le bouton de traduction initialement

# Créer l'onglet "Traduction" (Onglet 3)

def setup_tab3(fichier_txt=None):
    """configure le tab3 avec un affichage de fichier texte optionnel."""
    global canvas_imported, text_widget2, photo, max_width_image, max_height_image, TAB3_etat

    # Canvas pour afficher les images
    canvas_imported = tk.Canvas(tab3, width=max_width_image, height=max_height_image,bg="#333333")
    canvas_imported.grid(row=0, column=0, padx=10, pady=10, rowspan=5)  # Augmentation du rowspan pour tous les éléments
    canvas_imported.create_image(0, 0, anchor=tk.NW, image=photo)

    # Etiquette de traduction placée tout en haut
    translation_label = tk.Label(tab3, text="La traduction proposée a été enregistrée.",background="#333333", foreground="white")
    translation_label.grid(row=1, column=1, padx=(0, 0), pady=(0, 775))  # Réduction du padding pour un meilleur alignement

    # Etiquette de traduction placée tout en haut
    translation_label = tk.Label(tab3, text="Vous pouvez effectuer des modifications si nécessaire.",background="#333333", foreground="white")
    translation_label.grid(row=1, column=1, padx=(0, 0), pady=(0, 725))  # Réduction du padding pour un meilleur alignement

    # Zone de texte avec une barre de défilement pour l'édition du texte
    txt_scroll_frame = tk.Frame(tab3)
    txt_scroll_frame.grid(row=1, column=1, padx=0, pady=100, sticky="nsew")
    text_widget2 = tk.Text(txt_scroll_frame, height=30, width=80)
    scrollbar = tk.Scrollbar(txt_scroll_frame, command=text_widget2.yview)
    text_widget2.config(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Etiquette pour les instructions de sauvegarde du fichier placée en dessous de la zone de texte
    correction_label = tk.Label(tab3,
                                text="Une fois les modifications faites, vous pouvez enregistrer et cela écrasera la traduction proposée initialement.",background="#333333", foreground="white",)
    correction_label.grid(row=1, column=1, padx=(0, 0), pady=(725, 0))  # Ajustement du padding

    # Bouton pour sauvegarder le texte, placé en dessous de l'étiquette de correction
    save_text_button = tk.Button(tab3, text="Sauvegarder la traduction modifiée.", command=save_text)
    save_text_button.grid(row=1, column=1, padx=(0, 0), pady=(800, 0))  # Ajustement du padding

    # Charge le texte depuis un fichier si fourni
    if fichier_txt:
        with open(fichier_txt, 'r', encoding='utf-8') as file:
            text_content = file.read()
            text_widget2.insert(tk.END, text_content)
    
    TAB3_etat=TAB3_etat+1

# Créer l'onglet "Comptabilité" (Onglet 4)
image_frame = tk.Frame(tab4)

# Menus déroulants pour sélectionner l'année et (optionel) le mois:
label_mois = tk.Label(tab4, text="Mois:", bg='#333333', fg='white').grid(row=0, column=0, padx=padding_x_first_r, pady=30)
liste_mois = ('tous', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre',
              'novembre', 'décembre',)
(accounting_month_entry := ttk.Combobox(tab4, values=liste_mois, style="Light.TCombobox")).grid(row=0, column=1, padx=padding_x_acc, pady=30)

label_annee = tk.Label(tab4, text="Année:", bg='#333333', fg='white').grid(row=0, column=2, padx=padding_x_acc, pady=30)
liste_annees = (2018, 2019, 2020, 2021, 2022, 2023, 2024)
(accounting_year_entry := ttk.Combobox(tab4, values=liste_annees, style="Light.TCombobox")).grid(row=0, column=3, padx=padding_x_acc, pady=30)

# Bouton pour afficher les montants correspondants au mois et à l'année sélectionnés
tk.Button(tab4, text="Afficher les montants", command=display_sums).grid(row=0, column=4, padx=padding_x_acc, pady=30)

# Affiche le mois et l'année sélectionnés en haut des colonnes (année n demandée et année n-1)
# Mois choisi
label_month_var = tk.StringVar(value=None)
(label_month_n := tk.Label(tab4, textvariable=label_month_var,background="#333333", foreground="white")).grid(row=1, column=1, padx=padding_x_acc,
                                                                     pady=(5, 0))
font = tkFont.Font(font=label_month_n['font']).actual()
label_month_n.configure(font=(font['family'], font['size'], 'bold'))
(label_month_n_1 := tk.Label(tab4, textvariable=label_month_var,background="#333333", foreground="white")).grid(row=1, column=2, padx=padding_x_acc,
                                                                       pady=(5, 0))
label_month_n_1.configure(font=(font['family'], font['size'], 'bold'))

# Année choisie n et année précédente n-1 (n_1)
label_year_n_var = tk.StringVar(value=None)
(label_year_n := tk.Label(tab4, textvariable=label_year_n_var,background="#333333", foreground="white")).grid(row=2, column=1, padx=padding_x_acc,
                                                                     pady=(0, 10))
label_year_n.configure(font=(font['family'], font['size'], 'bold'))

label_year_n_1_var = tk.StringVar(value=None)
(label_year_n_1 := tk.Label(tab4, textvariable=label_year_n_1_var,background="#333333", foreground="white")).grid(row=2, column=2, padx=padding_x_acc,
                                                                         pady=(0, 10))
label_year_n_1.configure(font=(font['family'], font['size'], 'bold'))

# Initialise la liste des montants par catégorie
somme_montant_cat_year_n = []  # Liste des montants cumulés pour chaque catégorie pour la période n donnée
somme_montant_cat_year_n_1 = []  # Liste des montants cumulés pour chaque catégorie pour la période n-1
for i in range(length_expense_category):
    somme_montant_cat_year_n.append(None)
    somme_montant_cat_year_n_1.append(None)

# Pour chaque catégorie de dépense:
for i in range(length_expense_category):
    # Définit la catégorie que l'on va rechercher
    categorie = liste_categorie_depense[i]

    # Affiche les catégories
    tk.Label(tab4, text=categorie, bg='#333333', fg='white').grid(row=i + 3, column=0, padx=padding_x_first_r, pady=5)
    somme_montant_cat_year_n[i] = tk.DoubleVar(value=None)
    tk.Label(tab4, textvariable=somme_montant_cat_year_n[i], bg='#333333', fg='white').grid(row=i + 3, column=1, padx=padding_x_acc, pady=5)
    somme_montant_cat_year_n_1[i] = tk.DoubleVar(value=None)
    tk.Label(tab4, textvariable=somme_montant_cat_year_n_1[i], bg='#333333', fg='white').grid(row=i + 3, column=2, padx=padding_x_acc, pady=5)

# Affiche le total des catégories
(label_sum := tk.Label(tab4, text='Total', bg='#333333', fg='white')).grid(row=length_expense_category + 4, column=0,
                                                 padx=padding_x_first_r, pady=10)
label_sum.configure(font=(font['family'], font['size'], 'bold'))

# Total de l'année n
total_year_n = tk.DoubleVar(value=None)
(label_sum_n := tk.Label(tab4, textvariable=total_year_n)).grid(row=length_expense_category + 4, column=1,
                                                                padx=padding_x_acc, pady=5)
label_sum_n.configure(font=(font['family'], font['size'], 'bold'))

# Total de l'année n - 1
total_year_n_1 = tk.DoubleVar(value=None)
(label_sum_n_1 := tk.Label(tab4, textvariable=total_year_n_1)).grid(row=length_expense_category + 4, column=2,
                                                                    padx=padding_x_acc, pady=5)
label_sum_n_1.configure(font=(font['family'], font['size'], 'bold'))

# Liste déroulante permettant de sélectionner une catégorie et bouton permettant d'afficher le détail de la catégorie sélectionnée
tk.Label(tab4, text="Catégorie de dépense:", bg='#333333', fg='white').grid(row=2, column=3, padx=padding_x_acc, pady=5)
(expense_category_entry_acc := ttk.Combobox(tab4, values=liste_categorie_depense, style="Light.TCombobox")).grid(row=4, column=3,
                                                                                        padx=padding_x_acc, pady=5)

button_category_detail = tk.Button(tab4, text="Liste des factures", command=display_list_invoice)
button_category_detail.grid(row=5, column=3, padx=padding_x_acc, pady=5)
button_category_detail.config(state="disabled")  # Désactive le bouton

text_widget_acc = tk.Text(tab4, wrap="word", width=40, height=30)
text_widget_acc.grid(row=6, column=3, rowspan=length_expense_category + 4 - 6, padx=padding_x_acc, pady=5)
text_widget_acc.configure(font=(font['family'], font['size']))

# Zone de texte permettant d'entrer un identifiant de facture et bouton permettant d'afficher le détail de la facture
tk.Label(tab4, text="ID de la facture:", bg='#333333', fg='white').grid(row=3, column=4, padx=padding_x_acc, pady=5)
invoice_id_entry = tk.IntVar(value=None)
(invoice_id_acc := ttk.Entry(tab4, textvariable=invoice_id_entry)).grid(row=4, column=4, padx=padding_x_acc, pady=5)

button_invoice_detail = tk.Button(tab4, text="Détails de la facture", command=display_details_invoice)
button_invoice_detail.grid(row=5, column=4, padx=padding_x_acc, pady=5)

text_widget_details_facture = tk.Text(tab4, wrap="word", width=40, height=30)
text_widget_details_facture.grid(row=6, column=4, rowspan=length_expense_category + 4 - 6, padx=padding_x_acc, pady=5)
text_widget_details_facture.configure(font=(font['family'], font['size']))

# Bouton permettant d'afficher la facture dont l'identifiant a été entré
button_view_invoice = tk.Button(tab4, text="Voir la facture", command=display_invoice)
button_view_invoice.grid(row=19, column=4, padx=padding_x_acc, pady=0)

# Bouton permettant d'afficher la traduction de la facture dont l'identifiant a été entré
button_view_translation = tk.Button(tab4, text="Voir la traduction de la facture", command=display_invoice_translation)
button_view_translation.grid(row=20, column=4, padx=padding_x_acc, pady=0)

# Bouton permettant d'afficher la traduction de la facture dont l'identifiant a été entré
button_view_translation = tk.Button(tab4, text="Effacer la facture", command=delete_invoice)
button_view_translation.grid(row=21, column=4, padx=padding_x_acc, pady=0)

# Bouton permettant d'afficher la traduction de la facture dont l'identifiant a été entré
button_view_translation = tk.Button(tab4, text="Réinitialiser la fenêtre", command=initialisation_acc_full)
button_view_translation.grid(row=25, column=4, padx=padding_x_acc, pady=0)

tab_control.pack(expand=1, fill='both')

# Ajout de l'event binding, si on clique sur l'onglet 5 alors on actualise la tab
tab_control.bind("<<NotebookTabChanged>>", tab_selected)


def setup_tab5():
    global tab5, count, Var_stockage_cate

    # Création d'un canvas et de deux barres de défilement dans 'tab5'
    canvas = tk.Canvas(tab5, bg="#333333")
    v_scrollbar = ttk.Scrollbar(tab5, orient="vertical", command=canvas.yview)
    h_scrollbar = ttk.Scrollbar(tab5, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    # Placement des scrollbars et du canvas dans 'tab5'
    v_scrollbar.pack(side="right", fill="y")
    h_scrollbar.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    # Création d'un frame dans le canvas
    scrollable_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Données pour les combobox
    months = ["Choisir un mois"] + ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
                                    "septembre", "octobre", "novembre", "décembre"]
    years = ["Choisir une année", "Depuis toujours"] + [str(year) for year in range(2018, 2025)]

    #Initialisation d'une liste avec "Choisir une catégorie" suivi de chaque catégorie de dépense généralisé
    specific_categories = ["Choisir une catégorie"]  # Commence par ajouter "Choisir une catégorie" à la liste
    for categorie in liste_categorie_depense:
        specific_categories.append(categorie)  # Ajoute chaque catégorie à la liste

    # Configuration des widgets selon les catégories
    categories_left = [
        "Nombre de factures :", "Nombre de factures traduites (selon date d'émission) :",
        "Nombre de caractères traduits (API) :",
        "Nombre de conversions de devises effectuées ce mois-ci (API) :"
    ]
    categories_right = [
        "Catégorie la plus fréquente :", "Langues de traduction les plus fréquentes :", "Prix moyen des factures :",
        "Prix moyen d'une facture d'une catégorie précise :"
    ]

    # Texte par défaut pour les résultats
    default_result_text = "Sélectionnez une période."

    # Placement des widgets dans deux colonnes
    for i, category in enumerate(categories_left + categories_right):
        column_offset = 0 if category in categories_left else 2  # Utilisation de la colonne 2 pour la droite
        row_offset = i if column_offset == 0 else i - len(categories_left)

        # Label de catégorie
        label = tk.Label(scrollable_frame, text=category, font=('Helvetica', 14, 'bold'), background="#333333", foreground="white")
        label.grid(row=row_offset * 4, column=column_offset, padx=10, pady=10, sticky="w")

        # Colonne supplémentaire pour l'espacement
        scrollable_frame.grid_columnconfigure(1, minsize=50)  # Largeur minimale pour l'espacement.
        
        # Fonction appelée lors de la sélection d'une catégorie dans le Combobox.
        def on_category_select(event):
            global Var_stockage_cate
            Var_stockage_cate = specific_category_combobox.get()
            result_label.config(text="Catégorie sélectionnée : " + Var_stockage_cate)
            # Reset les choix de l'année a chaque changement de catégories.
            year_combobox.set("Choisir une année")  # Texte par défaut dans la Combobox des années
            month_combobox.set("Choisir un mois")  # Texte par défaut dans la Combobox des mois

        # Combobox spécifique pour "Prix moyen d'une facture d'une catégorie précise"
        if category == "Prix moyen d'une facture d'une catégorie précise :":
            # Combobox pour sélectionner la catégorie
            specific_category_combobox = ttk.Combobox(scrollable_frame, values=specific_categories, state="readonly",
                                          width=30, style="Light.TCombobox")
            specific_category_combobox.grid(row=row_offset * 4 + 1, column=column_offset, padx=10, pady=5)
            specific_category_combobox.set("Choisir une catégorie")

            # Liaison de la fonction à l'événement de sélection de la Combobox
            specific_category_combobox.bind("<<ComboboxSelected>>", on_category_select)
        

        # Affichage dynamique du nombre de changement de devises en cours
        if category == "Nombre de conversions de devises effectuées ce mois-ci (API) :":

            #Connexion à la BDD pour récupérer le curseur
            connection, cursor = connect_to_db()
            count=compte_conversion_devise_mois(cursor)

            count_label = tk.Label(scrollable_frame, text=str(count), font=('Helvetica', 12), bg='#333333', fg='white')
            count_label.grid(row=row_offset * 4 + 1, column=column_offset, padx=200, pady=10, sticky="w")

        else:
            # Combobox pour les années et les mois, et label pour les résultats
            year_combobox = ttk.Combobox(scrollable_frame, values=years, state="readonly", width=15, style="Light.TCombobox")
            month_combobox = ttk.Combobox(scrollable_frame, values=months, state="readonly", width=15, style="Light.TCombobox")
            result_label = ttk.Label(scrollable_frame, text=default_result_text, font=('Helvetica', 12), background='#333333', foreground='white')

            year_combobox.set("Choisir une année")  # Texte par défaut dans la Combobox des années
            month_combobox.set("Choisir un mois")  # Texte par défaut dans la Combobox des mois

            # Placement des Combobox et du label dans la grille
            year_combobox.grid(row=row_offset * 4 + 2, column=column_offset, padx=10, pady=5)
            month_combobox.grid(row=row_offset * 4 + 3, column=column_offset, padx=10, pady=5)
            result_label.grid(row=row_offset * 4 + 2, column=column_offset + 1, rowspan=2, padx=10)

            # Liaisons pour la sélection de l'année et du mois.
            # Lambda permet d'actualiser dynamiquement l'interface utilisateur en réponse aux actions de l'utilisateur, comme la sélection d'un élément dans une Combobox.
            year_combobox.bind("<<ComboboxSelected>>",lambda event, cat=category, res=result_label, ycb=year_combobox,
                                                      mcb=month_combobox: year_selection_changed(event, ycb,
                                                                                                    mcb, cat,
                                                                                                    res))
            month_combobox.bind("<<ComboboxSelected>>", lambda event, cat=category, res=result_label, ycb=year_combobox,
                                                       mcb=month_combobox: month_selection_changed(event,
                                                                                                      ycb, mcb,
                                                                                                      cat, res))
            




# Activation des fonctions pour lancer les règles de styles et désactiver l'onglet TAB3, et lancer les configurations de styles 'style_configure'
deactivate_tab(2)
style_configure()


# Configure le gestionnaire de fermeture
root.protocol("WM_DELETE_WINDOW", on_close)
# Lance la boucle principale de l'interface graphique
root.mainloop()
