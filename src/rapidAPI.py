import requests
from config import RAPID_API

def convertir_devises(montant, devise_base, devise_cible):
    # url de l'api pour la conversion de devises
    url = "https://currency-conversion-and-exchange-rates.p.rapidapi.com/convert"
    # paramètres de la requête : devise de départ, devise cible, montant
    querystring = {"from": devise_base, "to": devise_cible, "amount": montant}
    # en-têtes de la requête, incluant la clé api et l'hôte
    headers = {
        "X-RapidAPI-Key": RAPID_API,
        "X-RapidAPI-Host": "currency-conversion-and-exchange-rates.p.rapidapi.com"
    }

    # envoie de la requête get à l'api avec les en-têtes et les paramètres
    response = requests.get(url, headers=headers, params=querystring)
    # conversion de la réponse en json
    data = response.json()

    # vérifie si la requête a réussi
    if data['success']:
        # extrait le résultat de la conversion
        resultat_conversion = data['result']
        # affiche le résultat de la conversion
        print(f"{montant} {devise_base} est équivalent à {resultat_conversion:.2f} "
              f"{devise_cible} au taux de change actuel.")
        return resultat_conversion
    else:
        # affiche un message d'erreur si la requête a échoué
        print("il y a eu une erreur avec la requête de conversion.")
        return None
