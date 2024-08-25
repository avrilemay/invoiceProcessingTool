import cv2
import numpy as np

# fonction pour redimensionner l'image selon un facteur de mise à l'échelle
def resize_image(image, scale_factor):
    # calcule la nouvelle largeur
    width = int(image.shape[1] * scale_factor)
    # calcule la nouvelle hauteur
    height = int(image.shape[0] * scale_factor)
    # retourne l'image redimensionnée
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_CUBIC)

# fonction pour ajuster et valider les coordonnées des ROI selon le facteur de mise à l'échelle
def adjust_and_validate_roi(roi, scale_factor):
    # applique le facteur de mise à l'échelle aux coordonnées du ROI
    x1, y1, x2, y2 = [int(x * scale_factor) for x in roi]
    # retourne les coordonnées ajustées
    return x1, y1, x2, y2

# Fonctions pour redresser une image penchée, sur la base de la source ci-dessous, modifiées pour les besoins de l'application
#Source: https://becominghuman.ai/how-to-automatically-deskew-straighten-a-text-image-using-opencv-a0c30aed83df


# Détection de l'angle
def getSkewAngle(cvImage) -> float:
    # Prépare l'image, la copie, la convertit en "grayscale", applique blur et threshold
    newImage = cvImage.copy()
    gray = cv2.cvtColor(newImage, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Dilate le texte afin d'obtenir de faire ressortir les lignes et paragraphes
    # Applique un kernel plus grand sur l'axe X pour fusionner les caractères
    # et obtenir une ligne compacte sans espaces
    # Applique un kernel plus petit sur l'axe Y pour bien séparer les blocs de texte
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
    dilate = cv2.dilate(thresh, kernel, iterations=2)

    # Trouve les contours
    contours, hierarchy = cv2.findContours(dilate, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # Trie les contours par taille en ordre décroissant
    contours = sorted(contours, key = cv2.contourArea, reverse = True)
    # Pour chaque contour, dessine un rectangle en vert sur l'image (seulement pour la visualisation)
 #   for c in contours:
 #       rect = cv2.boundingRect(c)
 #       x,y,w,h = rect
 #       cv2.rectangle(newImage,(x,y),(x+w,y+h),(0,255,0),2)

    # Trouve les 8 contours les plus grands et détermine le rectangle minimum couvrant les données identifiées pour chacun de ces contours
    minAreaRect = []
    liste_angles = []
    n = 8                               # Nombre de contours les plus grands à examiner
    if len(contours) > n-1:
        i = 0
        while i < n + 1 :
            largestContour = contours[i]
            minAreaRect.append(cv2.minAreaRect(largestContour))     # détermine le rectangle minimum couvrant les données identifiées
            i += 1

        # Etablit la liste des angles pour les 8 contours les plus grands et détermine l'angle le plus fréquent de la liste
        for i in range(len(minAreaRect)-1):
            liste_angles.append(round(minAreaRect[i][-1],0))            # arrondit l'angle déterminé afin de faciliter la recherche de l'angle le plus fréquent
        angle = most_frequent(liste_angles)                         # cherche l'angle le plus fréquent parmi les 8

    # Si le nombre de contours trouvé est inférieur à 8, utilise le plus grand contour pour déterminer l'angle
    else:
        largestContour = contours[0]                # sélectionne le plus grand contour
        minAreaRect = cv2.minAreaRect(largestContour)
        angle = minAreaRect[-1]

    # Convertir l'angle en angle de rotation par rapport à une image droite
    if angle > 45:
        angle = angle - 90
    return -1.0 * angle

# Fait pivoter l'image autour de son centre
def rotateImage(cvImage, angle: float):
    newImage = cvImage.copy()
    # détermine le centre de l'image
    (h, w) = newImage.shape[:2]
    center = (w // 2, h // 2)
    # fait pivoter l'image autour de son centre
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    newImage = cv2.warpAffine(newImage, M, (w, h), flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    return newImage

# Détermine la valeur la plus fréquente d'une liste
def most_frequent(List):
    unique, counts = np.unique(List, return_counts=True)
    index = np.argmax(counts)
    return unique[index]