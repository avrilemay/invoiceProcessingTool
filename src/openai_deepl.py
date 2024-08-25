import deepl
from config import DEEPL_API_KEY1, DEEPL_API_KEY2, OPENAI_API_KEY
from bdd_SQL import *
from openai import OpenAI

def nettoyage_texte_txt(texte):
    """
    Utilise l'API de ChatGPT 3.5 turbo pour corriger le texte.
    :param texte: Le texte à corriger.
    :return: Le texte corrigé.
    """

    # si le texte est vide (ne contient que des espaces) ou très court, on renvoie tel quel
    if not texte.strip() or len(texte) < 20:
        return texte

    # création d'un client API à partir de la clé de config.py
    client = OpenAI(api_key=OPENAI_API_KEY)

    # création d'une requête de complétion à l'API de OpenAI
    completion = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {"role": "system",
             "content": "You are an assistant with exceptional French editorial skills, "
                        "capable of identifying and correcting typographical errors in the text."},
            {"role": "user",
             "content": f"Le texte est issu d'une facture."
                        f" Corrige les fautes de grammaires, les typos, les caractères isolés."
                        f" Si le texte est trop court pour faire des corrections, renvoie-le à "
                        f"l'identique sans rien corriger."
                        f" Renvoie uniquement le texte corrigé dans ta réponse, sans aucun "
                        f"commentaire ou ajout."
                        f" Le texte est: {texte}"

             }
        ]
    )

    # extraction du texte corrigé de la réponse de l'API
    reponse = completion.choices[0].message.content

    # on renvoie le texte corrigé
    return reponse


def traduction_maj_bdd(texte_a_trad, langue_cible, id_facture):
    """
    traduit le texte et enregistre les infos dans la base de données
    Arguments :
        texte_a_trad (str): texte à traduire.
        langue_cible (str): langue dans laquelle traduire.
        id_facture (int): ID de la facture associée.
    """

    # on traduit le texte
    texte_traduit = traduire_texte(texte_a_trad, langue_cible);

    # on récupère la connexion et le curseur
    connection, cursor = connect_to_db()

    # on enregistre la traduction dans la base de données (on passe texte_a_trad en
    # argument car c'est d'après le texte original qu'on compte le nombre de caractères traduits)
    traduction_facture(id_facture, connection, cursor, langue_cible, texte_a_trad)

    # ferme la connexion et le curseur
    fermeture_bdd(connection, cursor)

    # on renvoie le texte traduit
    return texte_traduit


def traduire_texte(texte, langue_cible):
    """
    Utilise l'API DeepL pour traduire le texte.
    Arguments :
        texte (str): texte à traduire.
        langue_cible (str): langue cible de la traduction.
    Retourne :
        str: texte traduit ou un message d'erreur si les quotas sont dépassés.
    """

    # on récupère la connexion et le curseur
    connection, cursor = connect_to_db()

    # on récupère le nombre de caractères traduit durant le mois calendaire
    caracteres_trad_mois = total_caracteres_mois(cursor)
    print(f"Il y a eu {caracteres_trad_mois} caractères traduits ce mois.")

    # ferme la connexion et le curseur
    fermeture_bdd(connection, cursor)

    # selon le nombre de caractères traduits, on choisit notre clé d'API
    if caracteres_trad_mois < 495000:
        cle_API = DEEPL_API_KEY1
    elif caracteres_trad_mois < 995000:
        cle_API = DEEPL_API_KEY2
    else:
        return "Caractères épuisés pour le mois."

    # configuration de l'API avec la clé et création d'un translator
    translator = deepl.Translator(cle_API)

    # on choisit la bonne option de langue à passer à l'API selon notre choix de langue_cible
    lang_cible = {'anglais': "EN-US", 'espagnol': "ES", 'allemand': "DE"}.get(langue_cible)

    try:
        result = translator.translate_text(
            text=texte,  # texte à traduire
            source_lang="FR",  # définit la langue source comme français
            target_lang=lang_cible,  # définit la langue cible (anglais, espagnol ou allemand)
            preserve_formatting=True,  # indique à l'API de préserver le formatage du texte original
            outline_detection=True,  # indique à l'API de détecter les points d'articulation du texte
            split_sentences='1',  # indique à l'API de diviser le texte en phrases
        )
        return result.text  # on retourne le texte traduit

    finally:
        translator.close()  # on ferme l'instance translator


def ecrire_dans_fichier(nom_fichier, texte):
    """
    Fonction pour écrire le texte dans un fichier
    :param nom_fichier: Le nom du fichier de sortie.
    :param texte: Le texte à écrire dans le fichier.
    :return: None
    """
    with open(nom_fichier, 'w', encoding='utf-8') as fichier:
        fichier.write(texte + "\n\n\n")

