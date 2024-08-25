import mysql.connector
import datetime
import calendar
from config import HOST_MYSQL, USER_MYSQL, PASSWORD_MYSQL, DB_MYSQL

# fonction de connexion à la base de données MySQL
def connect_to_db():
    # connexion à la base de données MySQL
    connection = mysql.connector.connect(
        # adresse du serveur
        host=HOST_MYSQL,
        # nom d'utilisateur de la base de données
        user=USER_MYSQL,
        # mot de passe de la base de données
        password=PASSWORD_MYSQL,
        # nom de la base de données
        database=DB_MYSQL
    )

    # création d'un curseur pour exécuter des commandes SQL
    cursor = connection.cursor()

    # retourne la connexion et le curseur
    return connection, cursor


# fonction pour enregistrer une facture dans la base de données
def enregistrer_facture(connection, cursor, date_facture, emetteur, montant_original,
                        devise_originale, montant_euros, categorie, test=0):
    # création de la table factures si elle n'existe pas déjà
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS factures 
        (id INT AUTO_INCREMENT PRIMARY KEY, 
        date_ajout_BDD DATE DEFAULT (CURRENT_DATE()),
        date_facture DATE,
        emetteur VARCHAR(255), 
        montant_original FLOAT, 
        devise_originale VARCHAR(255),
        montant_euros FLOAT,
        categorie VARCHAR(255),
        nb_caracteres_traduits INT, 
        langue_cible VARCHAR(255),
        est_test INT
        )''')

    # insertion des données dans la table (seulement pour l'enregistrement de la facture)
    cursor.execute(
        "INSERT INTO factures (date_facture, emetteur, montant_original, devise_originale, "
        "montant_euros, categorie, est_test) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (date_facture, emetteur, montant_original, devise_originale, montant_euros, categorie, test))

    # validation des modifications de la base de données
    connection.commit()

    # récupération de l'identifiant de la dernière facture insérée
    id_facture = cursor.lastrowid

    # renvoie l'ID de la dernière facture ou None si invalide
    return id_facture


# fonction qui ajoute les données relatives à la traduction pour une facture déjà enregistrée
def traduction_facture(id_facture, connection, cursor, langue_cible, texte):
    # calcul du nombre de caractères du texte
    nb_caracteres = len(texte)

    # mise à jour de la table factures avec les données de la traduction (pour une facture déjà existante)
    cursor.execute(
        "UPDATE factures SET langue_cible = %s, nb_caracteres_traduits = %s WHERE id = %s",
        (langue_cible, nb_caracteres, id_facture))

    # on enregistre les modifications
    connection.commit()


# fonction pour compter le nombre de factures traitées pendant une période donnée
def nb_facture_traitees(mois, annee, cursor):
    # détermination de la date de début de la période
    debut, fin = temporalite(mois, annee)

    # requête pour obtenir le nombre de factures traitées pour la période donnée
    query = """
    -- sélectionne et compte le nombre d'identifiants uniques de factures
    SELECT COUNT(id) 
    -- à partir de la table 'factures'
    FROM factures 
    -- seulement les factures traitées après une date spécifiée
    WHERE date_facture >= %s AND date_facture <= %s
    """

    # on lance la requête avec en argument la période de début
    cursor.execute(query, (debut, fin,))

    # renvoie le nombre de facture traitées dans l'intervalle de temps
    resultat = cursor.fetchone()
    if resultat is not None and resultat[0] is not None:
        return int(resultat[0])
    else:
        return 0


# fonction pour calculer le prix moyen des factures sur une période donnée
def prix_moyen_facture(mois, annee, cursor):
    # détermination de la date de début de la période
    debut, fin = temporalite(mois, annee)

    # requête pour obtenir le prix moyen des factures pour la période donnée
    query = """
    -- calcule la moyenne des montants des factures
    SELECT CAST(AVG(montant_euros) AS FLOAT) 
    -- à partir de la table 'factures'
    FROM factures 
    -- seulement à partir d'une date donnée
    WHERE date_facture >= %s AND date_facture <= %s
    """

    # on lance la requête avec le début de la période donnée en argument
    cursor.execute(query, (debut, fin,))

    # renvoie le prix moyen des factures pour l'intervalle de temps
    resultat = cursor.fetchone()
    if resultat is not None and resultat[0] is not None:
        return float(resultat[0])
    else:
        return float(0)


# fonction pour calculer le prix moyen d'un type de facture sur une période donnée
def prix_moyen_facture_categorie(mois, annee, categorie, cursor):
    # détermination de la date de début de la période
    debut, fin = temporalite(mois, annee)

    # requête pour obtenir le prix moyen d'un type de facture sur une période donnée
    query = """
    -- calcule la moyenne des montants des factures
    SELECT CAST(AVG(montant_euros) AS FLOAT) 
    -- à partir de la table 'factures'
    FROM factures 
    -- seulement à partir d'une date donnée et pour une catégorie donnée
    WHERE date_facture >= %s AND date_facture <= %s AND categorie = %s
    """

    # lance la requête et passe la période donnée et la catégorie en arguments
    cursor.execute(query, (debut, fin, categorie,))

    # renvoie le prix moyen pour le type de facture
    resultat = cursor.fetchone()
    if resultat is not None and resultat[0] is not None:
        return float(resultat[0])
    else:
        return float(0)


# fonction pour compter le nombre total de caractères traduits
def nb_caracteres_traduits(mois, annee, cursor):
    # détermination de la date de début de la période
    debut, fin = temporalite(mois, annee)

    # requête pour obtenir le nombre total de caractères traduits sur une période donnée
    query = """
    -- additionne tous les caractères traduits 
    SELECT SUM(nb_caracteres_traduits) 
    -- à partir de la table 'factures'
    FROM factures 
    -- seulement à partir d'une date donnée 
    -- on utilise date_ajout_BDD en raison de la limitation de 500 000 caractères par mois de DeepL
    WHERE date_ajout_BDD >= %s AND date_ajout_BDD <= %s
    """

    # lance la requête et passe la période donnée en argument
    cursor.execute(query, (debut, fin,))

    # on renvoie le nombre total de caractères traduits sur la période
    resultat = cursor.fetchone()
    if resultat is not None and resultat[0] is not None:
        return int(resultat[0])
    else:
        return int(0)





def frequence_toutes_langues_cibles(mois, annee, cursor):
    # détermination de la date de début de la période
    debut, fin = temporalite(mois, annee)

    # requête pour obtenir la fréquence en % d'utilisation de chaque langue cible pour les
    # traductions sur une période donnée
    query = """
    -- sélectionne la colonne 'langue_cible' pour afficher la langue des traductions
    SELECT langue_cible,    
    -- compte le nombre total de traductions pour chaque langue cible
    COUNT(*) AS nombre_traductions,
    -- calcule le pourcentage de traductions pour chaque langue par rapport au total des traductions
        -- sous-requête pour compter le total des traductions ayant une langue cible non nulle depuis la date spécifiée
    COUNT(*) * 100.0 / GREATEST(1, (SELECT COUNT(*) FROM factures WHERE date_facture >= %s AND 
    date_facture <= %s AND langue_cible IS NOT NULL)) AS pourcentage
    -- à partir de la table 'factures'
    FROM factures
    -- filtre les factures ajoutées depuis une date donnée où la langue cible est spécifiée
    WHERE date_facture >= %s AND date_facture <= %s AND langue_cible IS NOT NULL
    -- groupe les résultats par langue cible pour faire les agrégations
    GROUP BY langue_cible;
    """

    # exécute la requête en passant la période donnée en argument 2 fois (car il y a une sous-requête)
    cursor.execute(query, (debut, fin, debut, fin,))

    # récupère tous les résultats
    resultats = cursor.fetchall()

    # construire la chaîne de résultat (on ignore le nb de traductions)
    str_resultat = ', '.join(f"{langue}: {float(pourcentage):.2f}%"
                                           for langue, _, pourcentage in resultats)

    # retourne le résultat
    if str_resultat is not None:
        return str_resultat
    else:  # sinon un message
        return "Aucune donnée à afficher"


# fonction pour calculer le montant cumulé des factures par catégorie sur une période donnée
def somme_factures_categorie(mois, annee, categorie, cursor):
    # détermination de la date de début de la période
    debut, fin = temporalite(mois, annee)

    # requête pour obtenir le prix moyen d'un type de facture sur une période donnée
    query = """
    -- calcule la moyenne des montants des factures
    SELECT CAST(SUM(montant_euros) AS FLOAT)
    -- à partir de la table 'factures'
    FROM factures 
    -- seulement à partir d'une date donnée et pour une catégorie donnée
    WHERE date_facture >= %s AND date_facture <= %s AND categorie = %s
    """

    # lance la requête et passe la période donnée et la catégorie en arguments
    cursor.execute(query, (debut, fin, categorie,))

    # renvoie la somme des factures pour le type de facture
    resultat = cursor.fetchone()
    if resultat is not None and resultat[0] is not None:
        return float(resultat[0])
    else:
        return float(0)


# fonction pour récupérer le nombre total de caractères traduits ce mois-ci
def total_caracteres_mois(cursor):
    # Calculer le début du mois actuel
    debut_du_mois = datetime.date.today().replace(day=1)

    # Requête pour obtenir la somme des caractères traduits depuis le début du mois
    query = """
    SELECT SUM(nb_caracteres_traduits) 
    FROM factures 
    WHERE date_ajout_BDD >= %s
    """
    cursor.execute(query, (debut_du_mois,))

    total_caracteres_mois = cursor.fetchone()
    if total_caracteres_mois is not None and total_caracteres_mois[0] is not None:
        total_caracteres_mois = total_caracteres_mois[0]
    else:
        total_caracteres_mois = 0

    return int(total_caracteres_mois)


def afficher_informations_facture(cursor, id_facture):
    query = """
            SELECT id, date_ajout_BDD, date_facture, emetteur, montant_original, devise_originale, 
                   montant_euros, categorie, nb_caracteres_traduits, langue_cible 
            FROM factures 
            WHERE id = %s;
            """

    # Exécution de la requête avec l'ID de la facture
    cursor.execute(query, (id_facture,))

    # Récupération des résultats
    result = cursor.fetchone()

    if result is not None and len(result) > 0:
        resultat_formatte = (
            f"ID Facture: {result[0]}\n"
            f"Date d'ajout dans la BDD: {result[1]}\n"
            f"Date de la facture: {result[2]}\n"
            f"Émetteur: {result[3]}\n"
            f"Montant original: {result[4]} {result[5]}\n"
            f"Montant en euros: {result[6]}\n"
            f"Catégorie: {result[7]}\n"
            f"Nombre de caractères traduits: {result[8]}\n"
            f"Langue cible de la traduction: {result[9]}\n"
        )

    else:
        resultat_formatte = f"Aucune facture trouvée avec l'identifiant facture {id_facture}"

    return resultat_formatte


def details_factures_categorie(categorie, mois, annee, cursor):
    # détermination de la date de début et de fin de la période
    debut, fin = temporalite(mois, annee)

    # exécuter la requête pour obtenir les factures
    query = """
    SELECT *
    FROM factures
    WHERE date_facture >= %s AND date_facture <= %s AND categorie = %s;
    """
    cursor.execute(query, (debut, fin, categorie))

    # récupérer les résultats
    resultats = cursor.fetchall()

    # vérifier si des résultats ont été trouvés
    if resultats:
        # on crée une str vide pour commencer
        resultat_formatte = ""
        for resultat in resultats:
            resultat_formatte += (
                f"ID Facture: {resultat[0]}\n"
                f"Date de la facture: {resultat[2]}\n"
                f"Émetteur: {resultat[3]}\n"
                f"Montant original: {resultat[4]} {resultat[5]}\n"
                f"Montant en euros: {resultat[6]}\n"
                "\n"  # ajoute une ligne vide entre les factures
            )
        return resultat_formatte
    else:
        resultat_formatte = "Aucune facture trouvée pour cette période."
        return resultat_formatte

def compte_conversion_devise_mois(cursor):

    # calculer le début du mois actuel
    debut_du_mois = datetime.date.today().replace(day=1)

    query = """
    SELECT COUNT(*)
    FROM factures
    WHERE date_ajout_BDD >= %s AND devise_originale != 'EUR';
    """
    cursor.execute(query, (debut_du_mois, ))

    # récupérer les résultats
    resultat = cursor.fetchone()
    if resultat is not None and resultat[0] is not None:
        return int(resultat[0])
    else:
        return int(0)


# fonction pour la catégorie de facture la plus fréquente
def categorie_plus_frequente(mois, annee, cursor):
    # détermination de la date de début de la période
    debut, fin = temporalite(mois, annee)

    # requête pour obtenir la catégorie la plus fréquente pour une période donnée
    query = """
    -- sélectionne la colonne 'categorie' 
    SELECT categorie,
     -- compte le nombre de factures par catégorie
    COUNT(*) AS nombre_categorie
    FROM factures
    -- seulement pour une période donnée
    WHERE date_facture >= %s AND date_facture <= %s
    -- groupe les résultats par catégorie pour effectuer les calculs
    GROUP BY categorie;
    -- classe du plus grand au plus petit nombre
    ORDER BY nombre_categorie DESC
    -- on prend le plus grand nombre (ne gère pas les égalités)
    LIMIT 1;
    """

    # lance la requête
    cursor.execute(query, (debut, fin))

    # récupérer les résultats
    resultat = cursor.fetchone()
    if resultat is not None and resultat[0] is not None:
        cursor.fetchall()
        # accède à la première valeur du tuple qui correspond au nom de la cat la + fréquente
        return resultat[0]
    else:
        return None


# fonction pour calculer le nombre de factures traduites
def nb_factures_traduites(mois, annee, cursor):
    # détermination de la date de début de la période
    debut, fin = temporalite(mois, annee)

    # requête pour obtenir le nb de factures traduites
    query = """
    -- compte le nombre total de traductions   
    SELECT COUNT(*) AS nombre_traductions
    -- à partir de la table 'factures'
    FROM factures
    -- filtre les factures ajoutées depuis une date donnée où la langue cible est spécifiée
    WHERE date_facture >= %s AND date_facture <= %s AND langue_cible IS NOT NULL
    """

    # lance la requête
    cursor.execute(query, (debut, fin, ))

    # récupérer les résultats
    resultat = cursor.fetchone()
    if resultat is not None and resultat[0] is not None:
        # retourne la deuxième colonne qui contient le compte
        return int(resultat[0])
    else:
        return int(0)


# renvoie la catégorie d'une facture
def afficher_categorie_facture(cursor, id_facture):
    query = """
            SELECT categorie 
            FROM factures 
            WHERE id = %s;
            """

    # exécution de la requête avec l'ID de la facture
    cursor.execute(query, (id_facture,))

    # récupération du résultat
    resultat = cursor.fetchone()

    if resultat is not None and resultat[0] is not None and len(resultat) > 0:
        return resultat[0]
    else:
        return "Aucune facture trouvée avec cet ID."



# affiche la date d'une facture
def afficher_date_facture(cursor, id_facture):
    query = """
            SELECT date_facture 
            FROM factures 
            WHERE id = %s;
            """

    # Exécution de la requête avec l'ID de la facture
    cursor.execute(query, (id_facture,))

    # Récupération des résultats
    result = cursor.fetchone()
    if result is not None and result[0] is not None and len(result) > 0:
        return result[0]
    else:
        return "Aucune facture trouvée avec cet ID."




# fonction pour supprimer une facture
def supprimer_facture(id_a_supp, cursor, connection):

    # requête pour supprimer la facture dont l'id est entré en arg
    query = """
    -- on supprime de la table factures
    DELETE FROM factures
    -- la facture dont l'id matche 
    WHERE id = %s
    """

    # on lance la requête
    cursor.execute(query, (id_a_supp,))
    # on l'enregistre
    connection.commit()


# fonction pour déterminer la temporalité (toujours, année, mois)
def temporalite(mois, annee):
    # gestion des cas pour toutes les factures depuis le début
    if mois == None and annee == "toutes":
        # début de la période donnée: 1er janvier 2018
        date_debut = datetime.date.today().replace(day=1, month=1, year=2018)
        date_fin = datetime.date.today()
        return date_debut, date_fin

    # gestion des cas pour une année spécifique entière
    elif (mois == None or mois == "tous") and annee != "toutes" and annee:
        # début de la période donnée: le début de l'année courante
        date_debut = datetime.date(year=int(annee), month=1, day=1)
        date_fin = datetime.date(year=int(annee), month=12, day=31)
        return date_debut, date_fin

    # gestion des cas pour un mois spécifique dans une année
    elif mois and annee != "toutes" and annee:
        # dico pour convertir nom mois en numéro
        mois_dict = {
            "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5,
            "juin": 6, "juillet": 7, "août": 8, "septembre": 9,
            "octobre": 10, "novembre": 11, "décembre": 12
        }

        # vérifie si le mois existe dans le dico
        if mois in mois_dict:
            # convertit l'année en entier
            annee_int = int(annee)
            # convertir le mois en entier
            mois_int = mois_dict[mois]
            # crée un objet date pour le premier jour du mois
            date_debut = datetime.date(annee_int, mois_int, 1)
            # obtient le dernier jour du mois avec monthrange (indice 0 = jour semaine)
            dernier_jour = calendar.monthrange(annee_int, mois_int)[1]
            # crée objet date avec la fin du mois
            date_fin = datetime.date(annee_int, mois_int, dernier_jour)
            # retourne la date de début et la date de fin du mois
            return date_debut, date_fin

    # erreur si mois spécifique mais toutes les années
    elif (mois != None or mois != "tous") and annee == "toutes":
        print("Veuillez sélectionner une année")

    # erreur si autre chose
    else:
        print("Entrée invalide")


# fonction de fermeture de la connexion à la base de données
def fermeture_bdd(connection, cursor):
    # on ferme le curseur
    cursor.close()
    # on ferme la connexion à la base de données
    connection.close()


def supprimer_test():

    # récupère la connexion et le curseur
    connection, cursor = connect_to_db()

    # requête pour supprimer les entrées de tests
    query = """
    -- on supprime de la table factures
    DELETE FROM factures
    -- les entrées dont la valeur de la colonne est_test est égale à 1
    WHERE est_test = 1
    """

    # on lance la requête
    cursor.execute(query)
    # on l'enregistre
    connection.commit()
    # on ferme la connexion et le curseur
    fermeture_bdd(connection, cursor)
