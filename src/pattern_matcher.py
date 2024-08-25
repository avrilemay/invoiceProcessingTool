import shutil
from datetime import datetime
import dateparser
import re
import os


# Dictionnaire pour convertir les numéros de mois en noms français
month_names = {"01": "Janvier", "02": "Fevrier", "03": "Mars",
        "04": "Avril", "05": "Mai", "06": "Juin",
        "07": "Juillet", "08": "Aout", "09": "Septembre",
        "10": "Octobre", "11": "Novembre", "12": "Decembre"}

# Crée le fichier trie accueillant les fichiers finaux et triés par année, mois et type de dépense
sort_folder = "trie_doc"  # nom du dossier de sortie
if not os.path.exists(sort_folder):
    os.makedirs(sort_folder)  # crée le dossier s'il n'existe pas

def get_categorie(content):
    # Dictionnaire des règles avec expressions régulières pour chaque catégorie
    # SI MODIFICATION, IL FAUT EGALEMENT MODIFIER la variable globale liste_categorie_depense dans l'UI
    categories = {
        'Alimentaire': r'\b(alimentaire|supermarché|Carrefour|ED|Casino|Lidl|Tesco|Aldi|Auchan|'
                       r'Monoprix|épicerie|nourriture|Costco|Intermarché|Leclerc|Franprix|'
                       r'Super U|Leader Price|Géant Casino|Dia|Biocoop|produits frais|fromage|'
                       r'viande|poisson|fruits)\b',
        'Ameublement': r'\b(ameublement|IKEA|Maisons du Monde|Conforama|meuble|décoration|ameubler|'
                       r'décorer|Roche Bobois|Maisons du Monde|Habitat|Gautier|Fly|Cinna|BoConcept '
                       r'ameublement|décor)\b',
        'Assurances': r'\b(assurance|AXA|Allianz|Groupama|Maif|Macif|assuré|couverture|Mutuelle '
                      r'Générale|Hiscox|AXA Entreprises|Generali Professionnels|Assurances '
                      r'Agricoles|Groupama|Crédit Agricole Assurances|SMACL Assurances|La Parisienne '
                      r'Assurances|Direct Assurance|Matmutassurance|couverture|police)\b',
        'Bar': r'\b(bar|verre de vin|pression|pinte|cocktail|happy hours|happy hour|shot|shots|bière|'
               r'alcool|boisson|spiritueux|tapas|pub)\b',
        'Bricolage': r'\b(bricolage|Castorama|Leroy Merlin|Brico Dépôt|outils|jardinage|peinture|'
                     r'quincaillerie|matériaux de construction|scie|perceuse|martelage|clouage|'
                     r'vissage|menuiserie)\b',
        'Cosmétiques': r'\b(cosmétiques|Sephora|parfum|L\'Oréal|Nuxe|mascara|fond de teint|lèvre|beauté|'
                       r'soin de la peau|crème|hydratant|maquillage|rouge à lèvres|blush|eyeliner|'
                       r'palette|contouring|skincare)\b',
        'Électronique': r'\b(électronique|Samsung|Apple|Sony|LG|Huawei|Iphone|iPad|tablette|ordinateur|'
                        r'télévision|équipement électronique|gadget|caméra|console de jeux|Xbox|'
                        r'PlayStation|Nintendo|smartwatch|GoPro|drone|enceinte|soundbar|casque audio|'
                        r'écouteurs|wifi|tplink|routeur|giga|gigabyte)\b',
        'Frais bancaires': r'\b(frais bancaires|transaction|ATM|distributeur automatique|distributeur)\b',
        'Livres': r'\b(livres|bibliothèque|FNAC|librairie|livre|bande dessinée|manga|roman|lecture|'
                  r'dictionnaire|publication|encyclopédie|BD|essai|poésie|littérature|auteur|'
                  r'édition|éditeur)\b',
        'Logement': r'\b(logement|loyer|appartement|maison|immobilier|caution|bail|habitation)\b',
        'Loisirs': r'\b(loisirs|cinéma|parc|Disneyland|Parc Astérix|divertissement|jeu|amusement|'
                   r'théâtre|spectacle|représentation|festival|concert|expo|exposition|musée|'
                   r'attraction|manège)\b',
        'Prêt-à-porter': r'\b(prêt-à-porter|vêtement|Zara|H&M|Galeries Lafayette|Uniqlo|habillement|'
                         r'couture|jean|pantalon|chemise|robe|jupon|sous-vêtement|pull|t-shirt|'
                         r'veste|costume|Levi\'s|Lacoste|The Kooples|Maje|Promod|Etam|Celio|Kiabi|'
                         r'Bonobo|undiz|habillement|vêtement|tee-shirt|débardeur|pull|legging|'
                         r'écharpe|brassière)\b',
        'Restauration': r'\b(restauration|restaurant|McDonald\'s|Burger King|Subway|menu|entrée|plat|'
                        r'dessert|repas|gastronomie|fast food|cuisine traditionnelle|cuisine locale|'
                        r'cantine|buffet|traiteur)\b',
        'Santé': r'\b(santé|pharmacie|clinique|docteur|radio|consultation|hôpital|CHU|Santéclair|'
                 r'médicament|médicaments|traitement|ordonnance|santé publique|AXA Santé|Allianz '
                 r'Santé|Harmonie Mutuelle|Mutuelle Générale|MACIF Santé|MAIF Santé|Groupama Santé|'
                 r'AG2R La Mondiale|MGEN|April Santé)\b',
        'Service': r'\b(service|réparation|entretien|taux horaire|prestation|service à domicile|'
                   r'à domicile|artisan|technicien|professionnel|aide|ménage|plomberie|électricité|'
                   r'soutien)\b',
        'Services Publics': r'\b(consommation|électricité|gaz|EDF|Engie|GRDF|Veolia|Suez|Gaz de '
                            r'France|ENEDIS|'
                            r'Direct Energie|Total Direct Energie|Eau de Paris|Saur)\b',
        'Sport': r'\b(sport|gym|Decathlon|Nike|Adidas|tennis|sports|activité physique|fitness|running|'
                 r'muscu)\b',
        'Téléphonie': r'\b(téléphonie|Orange|SFR|Free|Free Mobile|Bouygues Telecom|mobile|smartphone|'
                      r'ligne téléphonique|La Poste Mobile|Coriolis Telecom|Prixtel|Red by SFR|Sosh|'
                      r'B&YOU|ligne téléphonique|ligne téléphone|mobile|internet|fibre|fibre optique|'
                      r'ADSL|Go|Giga)\b',
        'Transport': r'\b(transportation|transports '
                     r'publics|transport public|SNCF|RATP|train|bus|billet|avion|Air '
                     r'France|Ryanair|EasyJet|Transavia|'
                     r'voyage|tramway|metro|covoiturage|voiture|Keolis|Transdev|Blablacar|CMA CGM|'
                     r'Corsica Ferries|Corsair International|Air Caraïbes|French Bee|La Compagnie|'
                     r'Eurolines|Ouibus|Blablabus|Lyon Turin Ferroviaire|Louis Dreyfus Armateurs|'
                     r'Compagnie du Ponant|ASL Airlines France)\b',
        'Travaux': r'\b(travaux|construction|main d\'oeuvre|matériel|réfection|matériaux|rénovation|'
                   r'maçonnerie|plomberie|électricité|chantier|ouvrier|bâtiment|ingénieur|architecte|'
                   r'réforme|réhabilitation|isolation|toiture|charpente|fondations|excavation)\b',
    }


    # parcourir chaque catégorie pour trouver un match (unpack la clé + la valeur régex)
    for category, regex in categories.items():
        # on cherche le réggex dans le contenu du texte
        match = re.search(regex, content, re.IGNORECASE)
        # si on a trouvé un mot dans le texte qui correspond à l'expression régex
        if match:
            # on renvoie la catégorie (+ le mot qui a permis l'association avec la cat pour tests)
            return category, match.group()

    # si aucun match n'est trouvé, renvoie la cat "Autre" et le mot "None"
    return 'Autre', None


# Lit le contenu d'un fichier et le retourne sous forme de chaîne.
def read_file_content(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()


def extract_amount(content):
    
    ############## Premier pattern ##############

    # Pattern spécifique pour le format "213,781.06" ou "21,781.06"( Pattern retrouvé dans le (
    # $))  car je n'arrivais pas a géneraliser sans que ca ne genère d'erreur dans les autre patterns.
    specific_pattern = r"\b(?<!Sous-)TOTAL\s+DE\s+LA\s+FACTURE:\s+(\d{1,3}(?:,\d{3})+\.\d{2})\b"

    # Recherche le pattern spécifique dans le contenu
    match = re.search(specific_pattern, content, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', '').strip())

    ############## Second pattern ##############
    
    # Nouveau pattern spécifique : cherche montant general si il y'en a un, il peut y'avoir ceci
    # dans les factures avec plusieurs items.
    specific_pattern2 = (r"\b(?<!Sous-)"
                            r"(montant general|Total général :)"
                            r"(?!.*HT)(?!.*Taxes)\s+(\d(?:\s?\d)*([.,]\d{1,2})?)\s*€?")
    
    # Recherche le deuxième pattern spécifique dans le contenu
    match = re.search(specific_pattern2, content, re.IGNORECASE)
    if match:
        # Si trouvé, retourne le montant en float après avoir remplacé les virgules par des
        # points et supprimé les espaces inutiles
        return clean_and_convert_to_float(match.group(2).replace(',', '.').replace(' ', '').strip())

    ############## Troisième pattern ##############

    # Pattern général : Cherche des montants avec des espaces comme séparateurs de milliers,
    # centaines, et cherche également les montants non séparés.
    general_pattern = (r"\b(?<!Sous-)"
                    r"(TOTAL NET|TOTAL NET |TOTAL NET :|TOTAL NET:|total du montant.*?"
                    r"|TOTAL|TOTAL |TOTAL :|TOTAL:"
                    r"|TOTAL A PAYER|TOTAL A PAYER |TOTAL A PAYER :|TOTAL A PAYER:"
                    r"|TOTAL À PAYER|TOTAL À PAYER |TOTAL À PAYER :|TOTAL À PAYER:"
                    r"|Total \(EUR\)|Total \(EUR\) |Total \(EUR\) :|Total \(EUR\):"
                    r"|TOTAL €|TOTAL € |TOTAL € :|TOTAL €:"
                    r"|TOTAL € NET|TOTAL € NET |TOTAL € NET :|TOTAL € NET:"
                    r"|TOTAL DU MONTANT|TOTAL DU MONTANT |TOTAL DU MONTANT :|TOTAL DU MONTANT:"
                    r"|MONTANT TOTAL|MONTANT TOTAL |MONTANT TOTAL :|MONTANT TOTAL:"
                    r"|MONTANT REEL|MONTANT REEL |MONTANT REEL :|MONTANT REEL:"
                    r"|MONTANT RÉEL|MONTANT RÉEL |MONTANT RÉEL :|MONTANT RÉEL:"
                    r"|TOTAL TTC|TOTAL TTC |TOTAL TTC :|TOTAL TTC:"
                    r"|TOTAL DE LA FACTURE|TOTAL DE LA FACTURE |TOTAL DE LA FACTURE :|TOTAL DE LA FACTURE:"
                    r"|PAYER TTC|PAYER TTC |PAYER TTC :|PAYER TTC:"
                    r"|NET A PAYER|NET A PAYER |NET A PAYER :|NET A PAYER:"
                    r"|NET À PAYER|NET À PAYER |NET À PAYER :|NET À PAYER:"
                    r"|NET A PAYER TTC|NET A PAYER TTC |NET A PAYER TTC :|NET A PAYER TTC:|NET A PAYER TTC'|NET A PAYER TTC' |NET A PAYER TTC' :|NET A PAYER TTC':"
                    r"|NET À PAYER TTC|NET À PAYER TTC |NET À PAYER TTC* |NET À PAYER TTC :|NET À "
                       r"PAYER TTC:|NET À PAYER TTC'|NET À PAYER TTC' |NET À PAYER TTC' :|NET À PAYER TTC':"
                    r"|SOMME A PAYER|SOMME A PAYER |SOMME A PAYER :|SOMME A PAYER:|SOMME A PAYER'|SOMME A PAYER' |SOMME A PAYER' :|SOMME A PAYER':"
                    r"|SOMME À PAYER|SOMME À PAYER |SOMME À PAYER :|SOMME À PAYER:|SOMME À PAYER'|SOMME À PAYER' |SOMME À PAYER' :|SOMME À PAYER':"
                    r"|SOMME A PAYER TTC|SOMME A PAYER TTC |SOMME A PAYER TTC :|SOMME A PAYER TTC:|SOMME A PAYER TTC'|SOMME A PAYER TTC' |SOMME A PAYER TTC' :|SOMME A PAYER TTC':"
                    r"|SOMME À PAYER TTC|SOMME À PAYER TTC |SOMME À PAYER TTC :|SOMME À PAYER TTC:|SOMME À PAYER TTC'|SOMME À PAYER TTC' |SOMME À PAYER TTC' :|SOMME À PAYER TTC':"
                    r"|Montant total à payer \(TTC\)|Montant total à payer \(TTC\) |Montant total à payer \(TTC\) :|Montant total à payer \(TTC\):"
                    r"|Montant total à payer|Montant total à payer |Montant total à payer :|Montant total à payer :"
                    r"|Montant total a payer \(TTC\)|Montant total a payer \(TTC\) |Montant total a payer \(TTC\) :|Montant total a payer \(TTC\):"
                    r"|Montant total a payer|Montant total a payer |Montant total a payer :|Montant total a payer :"
                    r"|TTC|TTC |TTC :|TTC:"
                    r"|TTC'|TTC' |TTC' :|TTC':"
                    r"|CB|CB |CB :|CB:"
                    r"|EUR |EUR)" 
                    r"(?!.*HT)(?!.*Taxes)\s+(\d(?:\s?\d)*)([.,]\d{1,2})?\s*€?")       

    # Recherche le deuxième pattern spécifique dans le contenu                                                     
    match = re.search(general_pattern, content, re.IGNORECASE)
    if match:
        # Si trouvé, extrait le montant
        amount = match.group(2)  
        if match.group(3):  # Vérifie s'il y a des décimales
            amount += match.group(3)
        # Retourne le montant en float après avoir supprimé les espaces et remplacé les virgules par des points
        return clean_and_convert_to_float(amount.replace(' ', '').replace(',', '.').strip())
    
    # Si aucun pattern n'est trouvé, retourne 0.0
    return float(0)


def clean_and_convert_to_float(amount_str):
    # vérifie s'il y a des points dans la chaîne
    if '.' in amount_str:
        # remplace tous les points par rien
        # sauf le dernier car on vérifie qu'il y a toujours un point qui suit "\."
        # avant le traitement (?=.*\.)
        amount_str = re.sub(r'\.(?=.*\.)', '', amount_str)
    return float(amount_str)


def extract_currency(content):
    # dictionnaires devises et correspondances ISO
    # noms longs en clé car sinon dupliqué
    currency_map = {
        # avec un \b cherche un mot, sans juste le contenu textuel
        r"\b(EUR)\b": "EUR",
        r"euros?|€": "EUR",
        r"\b(SFr\.)\b": "CHF",
        r"CHF|Francs? Suisses?": "CHF",
        r"\b(CAD|dollars? canadiens?|Dollar Canadien|Quebec|Québec|Canada)\b": "CAD",
        r"XOF|francs? CFA BCEAO|Franc CFA|FCFA|F CFA": "XOF",
        r"XAF|francs? CFA BEAC": "XAF",
        r"\b(XPF|francs? Pacifique|Franc CFP)\b": "XPF",
        r"XPF|francs? Pacifique|Franc CFP": "XPF",
        r"USD|\$|dollars?": "USD"
    }

    # parcourt le dictionnaire (clé/valeur) pour trouver une correspondance
    for nom_devise_long, code_devise in currency_map.items():
        # vérifie si le pattern correspond à une partie du texte
        if re.search(nom_devise_long, content, re.IGNORECASE):
            return code_devise  # retourne le code ISO de la devise trouvée

    return None # retourne None si aucune devise n'est trouvée


def save_document(filename, date_entry, amount_entry, expense_category, id_facture=None):

    global month_names, sort_folder
    print("***************** ENTRE DANS save_document***************")
    print(filename)                                      
    amount = amount_entry  # Montant de la facture
    date_str_format = date_entry.strftime('%d-%m-%Y')  # Formate la date d'entrée

    year = date_entry.strftime('%Y')  # Année extraite de la date
    month = month_names[date_entry.strftime('%m')]  # Mois extrait de la date et converti en nom de mois

    # Nettoyage du nom de fichier pour enlever le chemin
    base_filename = os.path.basename(filename)  # Récupère le nom de fichier sans le chemin
    file_extension = os.path.splitext(base_filename)[1]  # Récupère l'extension du fichier

    # Construit le nouveau nom de fichier
    new_filename = f"{id_facture}_{os.path.splitext(base_filename)[0]}_{amount}_{date_str_format}{file_extension}"
    
    # Construit le chemin du dossier de sauvegarde basé sur l'année, le mois et la catégorie de dépense
    directory = os.path.join(sort_folder, year, month, expense_category)
    print(f"Directory: {directory}")

    # Crée le dossier s'il n'existe pas déjà
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"Directory created: {directory}")
        
    # Construit le chemin complet du fichier à sauvegarder
    save_path = os.path.join(directory, new_filename)
    print(f"Save path: {save_path}")

    # Écrasement du fichier s'il existe déjà
    shutil.copy2(filename, save_path)

    # Copie le fichier original vers le chemin de sauvegarde
    print(f"Fichier sauvegardé sous : {save_path}")
    print("***************** SORT DE save_document***************")
    # Retourne le chemin du dossier de sauvegarde
    return directory
    

def extract_date(content):

    # accepte 29-04-2024 et 29/04/2024 et 29.04.2024 et 29 04 2024 et 29_04_2024
    match = re.search(r'\b(\d{1,2})[-_/. ](\d{1,2})[-_/. ](\d{4})\b', content)

    if match:
        # r'[]: on prend ce qui suit comme une raw string (pas d'échappement)
        # cherche tous les caractères qui appartiennent à '-', '_', '/', '.', ou un espace.
        # remplace les caractères par un tiret
        # renvoie la chaîne entière modifiée sous forme de string
        date_str = re.sub(r'[-_/. ]', '-', match.group(0))
        return date_str  # retourne la date comme une str

    # pour les formats 29 avril 2024 / 29 avril, 2024 / 29 avr. 2024
    match2 = re.search(r'\b(\d{1,2}) (\w+)\.?,? (\d{4})\b', content)
    if match2:
        try:
            # récupération du texte correspondant à la date
            date_text = match2.group(0)
            # convertit la date textuelle en français en objet DATE
            date_obj = dateparser.parse(date_text, languages=['fr'])

            # vérifier si date_obj est None
            if date_obj:
                # on formatte l'objet date en chaîne au format DD-MM-YYYY (plus user friendly) strF
                date_str_format = date_obj.strftime('%d-%m-%Y')
                return date_str_format  # retourne un str

        # en cas d'erreur, on passe
        except ValueError:
            pass
    # si aucun match: on renvoie "None"
    else:
        return None


def transf_datestr_obj(date_str):
    if date_str is not None:
        try:
            # convertit la str date_str au format DD-MM-YYYY en objet date (strP)
            date_obj = datetime.strptime(date_str, '%d-%m-%Y').date()
            return date_obj
        except ValueError:
            # retourne None si la date n'est pas dans le bon format
            # ou si ça ne correspond pas à une date (ex: 77-04-2024)
            return None
    return None  # retourne None si date_str est None

