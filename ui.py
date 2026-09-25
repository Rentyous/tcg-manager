"""Interactions utilisateur : affichage et saisies clavier.

Cf. Cahier des charges §6 (Menu utilisateur) et §4 (Architecture logicielle).
"""

from datetime import datetime

from models import Achat, Carte, CONDITIONS, aujourdhui, get_quantity

NOM_APPLICATION = "TCG Manager"
FORMAT_DATE_ISO = "%Y-%m-%d"
FORMAT_DATE_FR = "%d-%m-%Y"


def formater_date(date_iso):
    """Convertit une date ISO (AAAA-MM-JJ, telle que stockée) au format français JJ-MM-AAAA.

    Retourne la valeur telle quelle si elle n'est pas une date ISO valide.
    """
    try:
        return datetime.strptime(date_iso, FORMAT_DATE_ISO).strftime(FORMAT_DATE_FR)
    except ValueError:
        return date_iso


def lire_date(saisie):
    """Convertit une date saisie au format français JJ-MM-AAAA en date ISO (AAAA-MM-JJ)."""
    return datetime.strptime(saisie, FORMAT_DATE_FR).strftime(FORMAT_DATE_ISO)


def afficher_menu():
    """Affiche le menu principal (§6)."""
    print("=" * 31)
    print(f"      {NOM_APPLICATION}")
    print("=" * 31)
    print()
    print("1 - Afficher la collection")
    print("2 - Ajouter une carte")
    print("3 - Rechercher une carte")
    print("4 - Supprimer une carte")
    print("5 - Quitter")


def demander_choix():
    """Demande à l'utilisateur de choisir une option du menu."""
    return input("Choix : ")


def demander_nom_recherche():
    """Demande le nom (ou un extrait) de la carte à rechercher."""
    return input("Nom de la carte à rechercher : ")


def demander_rarete_filtre():
    """Demande une rareté pour filtrer une liste de cartes déjà trouvées (vide pour annuler)."""
    return input("Rareté (pour affiner, laissez vide pour annuler) : ")


def saisir_achat():
    """Demande les informations d'un achat (quantity, purchase_price, condition,
    purchase_date, purchase_location).

    Retourne un objet Achat. Propose l'échelle standard des états (CONDITIONS)
    à titre indicatif, mais accepte toute saisie libre (§8, pas de validation).
    La date d'achat se saisit au format JJ-MM-AAAA (stockée en ISO) et vaut la date
    du jour si l'utilisateur laisse la saisie vide.
    """
    quantity = int(input("Quantité : "))
    purchase_price = float(input("Prix d'achat : "))
    print(f"États possibles : {', '.join(CONDITIONS)}")
    condition = input("État (condition) : ")
    defaut = aujourdhui()
    saisie_date = input(f"Date d'achat (JJ-MM-AAAA, vide = {formater_date(defaut)}) : ").strip()
    purchase_date = lire_date(saisie_date) if saisie_date else defaut
    purchase_location = input("Lieu d'achat : ")
    return Achat(
        quantity=quantity,
        purchase_price=purchase_price,
        condition=condition,
        purchase_date=purchase_date,
        purchase_location=purchase_location,
    )


def saisir_identifiant_carte():
    """Demande uniquement les champs qui identifient une carte (get_id) : name,
    card_set_id, rarity, langue. Retourne le tuple (name, card_set_id, rarity, langue).

    À utiliser en premier lors d'un ajout : ces 4 champs suffisent à vérifier
    (via collection.trouver_carte) si la carte est déjà dans la collection,
    avant de redemander ou non le reste de ses informations.
    """
    name = input("Nom de la carte : ")
    card_set_id = input("Identifiant de set (card_set_id) : ")
    rarity = input("Rareté : ")
    langue = input("Langue : ")
    return name, card_set_id, rarity, langue


def saisir_details_carte(name, card_set_id, rarity, langue):
    """Demande le reste des informations d'une carte qui n'existe pas encore dans
    la collection (set, type, tcg, market_price, card_image) et son premier achat.

    `name`, `card_set_id`, `rarity`, `langue` viennent de saisir_identifiant_carte.
    Retourne un objet Carte, prêt à être passé à collection.ajouter_carte.
    """
    set_ = input("Set : ")
    type_ = input("Type : ")
    tcg = input("TCG : ")
    market_price = float(input("Prix du marché (market_price) : "))
    card_image = input("Image (URL ou chemin) : ")

    print("\nAchat de cette carte :")
    achat = saisir_achat()

    return Carte(
        name=name,
        card_set_id=card_set_id,
        set=set_,
        rarity=rarity,
        type=type_,
        langue=langue,
        tcg=tcg,
        market_price=market_price,
        card_image=card_image,
        purchases=[achat],
    )


def afficher_carte_detail(card):
    """Affiche une carte en détail : ses infos essentielles et ses achats."""
    print("-" * 40)
    print(f"{card.name} ({card.card_set_id})")
    print(f"  Set          : {card.set}")
    print(f"  Rareté       : {card.rarity}")
    print(f"  Type         : {card.type}")
    print(f"  Langue       : {card.langue}")
    print(f"  TCG          : {card.tcg}")
    print(f"  Prix marché  : {card.market_price}")
    print(f"  Image        : {card.card_image}")
    print(f"  Quantité     : {get_quantity(card)}")
    if card.purchases:
        print("  Achats :")
        for purchase in card.purchases:
            print(
                f"    - qty: {purchase.quantity}, "
                f"prix: {purchase.purchase_price}, "
                f"état: {purchase.condition}, "
                f"date: {formater_date(purchase.purchase_date) if purchase.purchase_date else 'non renseignée'}, "
                f"lieu: {purchase.purchase_location or 'non renseigné'}"
            )
    else:
        print("  Achats : aucun")


def demander_confirmation_suppression(card):
    """Affiche la carte à supprimer et demande une confirmation explicite (o/n).

    Action destructive et irréversible : une confirmation est demandée même si
    les validations de saisie sont hors périmètre MVP (§8) — ce n'est pas une
    validation de saisie mais un garde-fou sur une suppression.
    """
    afficher_carte_detail(card)
    reponse = input("Confirmer la suppression de cette carte ? (o/n) : ")
    return reponse.strip().lower() == "o"


def afficher_liste_cartes(cartes):
    """Affiche une liste de cartes en utilisant la présentation détaillée."""
    if not cartes:
        print("Aucune carte à afficher.")
        return
    for card in cartes:
        afficher_carte_detail(card)
    print("-" * 40)
