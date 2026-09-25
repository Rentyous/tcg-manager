"""Logique métier de gestion de la collection de cartes.

Cf. Cahier des charges §2.1 (Gestion de la collection) et §4 (Architecture logicielle).
"""

import storage
from models import get_id, get_quantity


def afficher_collection(collection):
    """Affiche toute la collection (une ligne par carte, infos essentielles)."""
    for card in collection:
        print(
            f"{card.name} - {card.set} ({card.card_set_id}) - {card.rarity} - "
            f"{card.tcg} - {card.langue} - qty: {get_quantity(card)} - "
            f"market_price: {card.market_price}"
        )


def rechercher_carte(collection, nom):
    """Retourne la liste des cartes dont le name contient `nom` (insensible à la casse)."""
    nom = nom.lower()
    return [card for card in collection if nom in card.name.lower()]


def filtrer_par_rarete(cartes, rarete):
    """Filtre une liste de cartes sur leur rarity (correspondance exacte, insensible à la casse)."""
    rarete = rarete.lower()
    return [card for card in cartes if card.rarity.lower() == rarete]


def trouver_carte(collection, name, card_set_id, rarity, langue):
    """Retourne la carte de `collection` dont get_id() == (name, card_set_id, rarity, langue),
    ou None si aucune ne correspond. Utilisé lors d'un ajout pour savoir si la carte
    existe déjà avant de redemander ses informations complètes."""
    for card in collection:
        if get_id(card) == (name, card_set_id, rarity, langue):
            return card
    return None


def ajouter_carte(collection, card):
    """Ajoute une nouvelle carte (avec son premier achat) à la collection et en base.

    Si une carte avec le même get_id() existe déjà dans `collection`, redirige
    automatiquement vers ajouter_exemplaires pour chaque achat de `card` : pas
    de doublon créé, les achats sont simplement rattachés à la carte existante.
    """
    for existing in collection:
        if get_id(existing) == get_id(card):
            for purchase in card.purchases:
                ajouter_exemplaires(collection, existing, purchase)
            return existing
    storage.add_card(card)
    collection.append(card)
    return card


def ajouter_exemplaires(collection, card, purchase):
    """Ajoute un nouvel achat à une carte déjà présente dans la collection.

    `card` sert à identifier la carte existante (via get_id) ; l'achat est
    ajouté à la carte trouvée dans `collection`, pas nécessairement à
    l'objet `card` passé en argument.
    """
    for existing in collection:
        if get_id(existing) == get_id(card):
            storage.add_purchase(existing, purchase)
            existing.purchases.append(purchase)
            return existing
    raise ValueError(f"Carte introuvable dans la collection : {get_id(card)}")


def supprimer_carte(collection, card):
    """Supprime une carte de la collection et de la base.

    `card` sert à identifier la carte existante (via get_id) dans
    `collection`. La suppression en base (storage.delete_card) est effectuée
    avant le retrait de `collection` (liste en mémoire).
    Lève ValueError si la carte n'est pas trouvée dans `collection`.
    """
    for existing in collection:
        if get_id(existing) == get_id(card):
            storage.delete_card(existing)
            collection.remove(existing)
            return
    raise ValueError(f"Carte introuvable dans la collection : {get_id(card)}")
