"""Tests unitaires de models.py (Achat, Carte, get_id, get_quantity, aujourdhui)."""

import unittest
from datetime import date

from models import Achat, Carte, aujourdhui, get_id, get_quantity


def creer_carte(**changements):
    """Construit une Carte de test ; `changements` remplace les valeurs par défaut."""
    valeurs = dict(
        name="Trafalgar Law",
        card_set_id="OP10-119",
        set="OP10",
        rarity="SEC",
        type="Personnage",
        langue="FR",
        tcg="One Piece",
        market_price=125.0,
        card_image="law.png",
    )
    valeurs.update(changements)
    return Carte(**valeurs)


class TestAujourdhui(unittest.TestCase):
    def test_aujourdhui_retourne_la_date_du_jour_au_format_iso(self):
        self.assertEqual(aujourdhui(), date.today().isoformat())


class TestAchat(unittest.TestCase):
    def test_date_par_defaut_est_la_date_du_jour_iso(self):
        achat = Achat(quantity=1, purchase_price=5.0, condition="Near Mint")
        self.assertEqual(achat.purchase_date, date.today().isoformat())

    def test_lieu_par_defaut_est_vide(self):
        achat = Achat(quantity=1, purchase_price=5.0, condition="Near Mint")
        self.assertEqual(achat.purchase_location, "")

    def test_date_et_lieu_explicites_sont_conserves(self):
        achat = Achat(2, 8.5, "Mint", purchase_date="2025-01-31", purchase_location="Cardmarket")
        self.assertEqual(achat.purchase_date, "2025-01-31")
        self.assertEqual(achat.purchase_location, "Cardmarket")


class TestCarte(unittest.TestCase):
    def test_purchases_est_vide_par_defaut(self):
        self.assertEqual(creer_carte().purchases, [])

    def test_purchases_nest_pas_partagee_entre_deux_cartes(self):
        carte_a = creer_carte(name="A")
        carte_b = creer_carte(name="B")
        carte_a.purchases.append(Achat(1, 1.0, "Mint"))
        self.assertEqual(carte_b.purchases, [])
        self.assertIsNot(carte_a.purchases, carte_b.purchases)


class TestGetId(unittest.TestCase):
    def test_get_id_retourne_name_set_id_rarete_langue(self):
        self.assertEqual(get_id(creer_carte()), ("Trafalgar Law", "OP10-119", "SEC", "FR"))

    def test_get_id_ignore_les_autres_champs(self):
        carte_a = creer_carte(market_price=1.0, card_image="a.png", tcg="X")
        carte_b = creer_carte(market_price=99.0, card_image="b.png", tcg="Y")
        self.assertEqual(get_id(carte_a), get_id(carte_b))

    def test_get_id_differe_si_la_rarete_change(self):
        self.assertNotEqual(get_id(creer_carte(rarity="SEC")), get_id(creer_carte(rarity="SR")))

    def test_get_id_differe_si_la_langue_change(self):
        self.assertNotEqual(get_id(creer_carte(langue="FR")), get_id(creer_carte(langue="EN")))


class TestGetQuantity(unittest.TestCase):
    def test_quantite_zero_sans_achat(self):
        self.assertEqual(get_quantity(creer_carte()), 0)

    def test_quantite_dun_seul_achat(self):
        carte = creer_carte()
        carte.purchases.append(Achat(3, 2.0, "Mint"))
        self.assertEqual(get_quantity(carte), 3)

    def test_quantite_somme_de_plusieurs_achats(self):
        carte = creer_carte()
        carte.purchases.extend([
            Achat(2, 8.5, "Near Mint"),
            Achat(1, 10.0, "Played"),
            Achat(4, 3.0, "Good"),
        ])
        self.assertEqual(get_quantity(carte), 7)


if __name__ == "__main__":
    unittest.main()
