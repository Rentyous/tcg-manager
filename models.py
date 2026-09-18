"""Structures de données (Carte, Achat) et fonctions utilitaires associées.

Cf. Cahier des charges §3 (Modèle de données) et §4 (Architecture logicielle).
"""

from dataclasses import dataclass, field

# Échelle standard TCG (§3), à titre de référence. Pas de validation de
# saisie ici : voir §8, hors périmètre du MVP.
CONDITIONS = ["Mint", "Near Mint", "Excellent", "Good", "Lightly Played", "Played", "Bad"]


@dataclass
class Achat:
    """Un achat : un lot d'exemplaires d'une carte dans un état donné."""

    quantity: int
    purchase_price: float
    condition: str


@dataclass
class Carte:
    """Une carte de la collection, avec l'historique de ses achats."""

    name: str
    card_set_id: str
    set: str
    rarity: str
    type: str
    langue: str
    tcg: str
    market_price: float
    card_image: str
    purchases: list[Achat] = field(default_factory=list)


def get_id(card):
    """Retourne l'identifiant d'une carte.

    Clé naturelle stable (name, card_set_id, rarity, langue) : ce sont les
    attributs qui distinguent deux impressions physiques différentes d'une
    même carte, utilisée par collection.py pour retrouver/dédupliquer une
    carte déjà présente dans la collection.
    """
    return (card.name, card.card_set_id, card.rarity, card.langue)


def get_quantity(card):
    """Calcule la quantité totale d'exemplaires d'une carte à partir de ses achats."""
    return sum(purchase.quantity for purchase in card.purchases)
