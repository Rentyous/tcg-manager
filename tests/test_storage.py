"""Tests unitaires de storage.py (SQLite).

Chaque test travaille sur une base temporaire (storage.DB_PATH est redirigé),
jamais sur le collection.db du projet.
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

import storage
from models import Achat, Carte


def creer_carte(name="Trafalgar Law", card_set_id="OP10-119", rarity="SEC", langue="FR", achats=None):
    """Construit une Carte de test avec tous ses champs renseignés."""
    if achats is None:
        achats = [Achat(2, 8.5, "Near Mint", "2026-09-25", "Cardmarket")]
    return Carte(
        name=name,
        card_set_id=card_set_id,
        set="OP10",
        rarity=rarity,
        type="Personnage",
        langue=langue,
        tcg="One Piece",
        market_price=125.5,
        card_image="https://exemple.test/law.png",
        purchases=achats,
    )


class BaseTemporaire(unittest.TestCase):
    """Redirige storage.DB_PATH vers une base jetable, restaurée après chaque test."""

    def setUp(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        ancien_chemin = storage.DB_PATH
        self.addCleanup(setattr, storage, "DB_PATH", ancien_chemin)
        self.db_path = Path(dossier.name) / "test.db"
        storage.DB_PATH = self.db_path

    def compter(self, table):
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        finally:
            conn.close()


class TestChargementEtAjout(BaseTemporaire):
    def test_base_vide_charge_une_collection_vide(self):
        self.assertEqual(storage.load_collection(), [])

    def test_base_vide_cree_le_fichier_et_les_tables(self):
        storage.load_collection()
        self.assertTrue(self.db_path.exists())
        self.assertEqual(self.compter("cards"), 0)
        self.assertEqual(self.compter("purchases"), 0)

    def test_aller_retour_add_card_load_collection_est_fidele(self):
        carte = creer_carte()
        storage.add_card(carte)
        self.assertEqual(storage.load_collection(), [carte])

    def test_aller_retour_conserve_image_date_et_lieu(self):
        storage.add_card(creer_carte())
        achat = storage.load_collection()[0].purchases[0]
        self.assertEqual(storage.load_collection()[0].card_image, "https://exemple.test/law.png")
        self.assertEqual(achat.purchase_date, "2026-09-25")
        self.assertEqual(achat.purchase_location, "Cardmarket")

    def test_aller_retour_conserve_plusieurs_achats(self):
        achats = [Achat(1, 5.0, "Mint", "2026-01-01", "Boutique"), Achat(3, 4.0, "Played", "2026-02-02", "")]
        storage.add_card(creer_carte(achats=achats))
        self.assertEqual(storage.load_collection()[0].purchases, achats)

    def test_add_card_retourne_lid_de_la_carte(self):
        self.assertIsInstance(storage.add_card(creer_carte()), int)

    def test_add_card_sans_achat(self):
        storage.add_card(creer_carte(achats=[]))
        self.assertEqual(storage.load_collection()[0].purchases, [])

    def test_plusieurs_cartes_gardent_chacune_leurs_achats(self):
        storage.add_card(creer_carte(achats=[Achat(1, 1.0, "Mint")]))
        storage.add_card(creer_carte(name="Luffy", card_set_id="OP01-001", achats=[Achat(9, 2.0, "Good")]))
        quantites = {c.name: c.purchases[0].quantity for c in storage.load_collection()}
        self.assertEqual(quantites, {"Trafalgar Law": 1, "Luffy": 9})


class TestAddPurchase(BaseTemporaire):
    def test_add_purchase_rattache_lachat_a_la_bonne_carte(self):
        law = creer_carte(achats=[])
        luffy = creer_carte(name="Luffy", card_set_id="OP01-001", achats=[])
        storage.add_card(law)
        storage.add_card(luffy)
        storage.add_purchase(luffy, Achat(3, 2.0, "Good", "2026-03-03", "Web"))
        par_nom = {c.name: c for c in storage.load_collection()}
        self.assertEqual(par_nom["Trafalgar Law"].purchases, [])
        self.assertEqual(par_nom["Luffy"].purchases, [Achat(3, 2.0, "Good", "2026-03-03", "Web")])

    def test_add_purchase_conserve_les_achats_precedents(self):
        storage.add_card(creer_carte())
        storage.add_purchase(creer_carte(), Achat(1, 1.0, "Mint", "2026-04-04", "Salon"))
        self.assertEqual(len(storage.load_collection()[0].purchases), 2)

    def test_add_purchase_retourne_lid_de_lachat(self):
        storage.add_card(creer_carte())
        self.assertIsInstance(storage.add_purchase(creer_carte(), Achat(1, 1.0, "Mint")), int)

    def test_add_purchase_carte_absente_leve_value_error(self):
        with self.assertRaises(ValueError):
            storage.add_purchase(creer_carte(), Achat(1, 1.0, "Mint"))

    def test_add_purchase_carte_absente_n_insere_rien(self):
        with self.assertRaises(ValueError):
            storage.add_purchase(creer_carte(), Achat(1, 1.0, "Mint"))
        self.assertEqual(self.compter("purchases"), 0)


class TestDeleteCard(BaseTemporaire):
    def test_delete_card_supprime_la_carte_et_ses_achats(self):
        carte = creer_carte(achats=[Achat(1, 1.0, "Mint"), Achat(2, 2.0, "Good")])
        storage.add_card(carte)
        storage.delete_card(carte)
        self.assertEqual(self.compter("cards"), 0)
        self.assertEqual(self.compter("purchases"), 0)

    def test_delete_card_respecte_les_cles_etrangeres(self):
        # foreign_keys est activé : supprimer cards avant purchases lèverait IntegrityError.
        carte = creer_carte()
        storage.add_card(carte)
        try:
            storage.delete_card(carte)
        except sqlite3.IntegrityError as erreur:
            self.fail(f"Violation de clé étrangère : {erreur}")

    def test_delete_card_ne_touche_pas_les_autres_cartes(self):
        law = creer_carte()
        luffy = creer_carte(name="Luffy", card_set_id="OP01-001", achats=[Achat(5, 3.0, "Mint")])
        storage.add_card(law)
        storage.add_card(luffy)
        storage.delete_card(law)
        self.assertEqual(storage.load_collection(), [luffy])
        self.assertEqual(self.compter("purchases"), 1)

    def test_delete_card_absente_leve_value_error(self):
        with self.assertRaises(ValueError):
            storage.delete_card(creer_carte())

    def test_connexion_active_les_cles_etrangeres(self):
        conn = storage.get_connection()
        try:
            self.assertEqual(conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        finally:
            conn.close()


class TestSaveCollection(BaseTemporaire):
    def test_save_collection_remplace_le_contenu_de_la_base(self):
        storage.add_card(creer_carte(name="Ancienne", card_set_id="X-1"))
        nouvelle = creer_carte()
        storage.save_collection([nouvelle])
        self.assertEqual(storage.load_collection(), [nouvelle])


class TestMigration(BaseTemporaire):
    def creer_ancienne_base(self):
        """Crée une base à l'ancien schéma : purchases sans purchase_date/purchase_location."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE cards (
                    id INTEGER PRIMARY KEY, name TEXT, card_set_id TEXT, "set" TEXT,
                    rarity TEXT, type TEXT, langue TEXT, tcg TEXT, market_price REAL, card_image TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE purchases (
                    id INTEGER PRIMARY KEY, card_id INTEGER, quantity INTEGER,
                    purchase_price REAL, condition TEXT,
                    FOREIGN KEY (card_id) REFERENCES cards(id)
                )
                """
            )
            conn.execute(
                "INSERT INTO cards VALUES (1, 'Trafalgar Law', 'OP10-119', 'OP10', 'SEC', "
                "'Personnage', 'FR', 'One Piece', 125.5, 'law.png')"
            )
            conn.execute(
                "INSERT INTO cards VALUES (2, 'Luffy', 'OP01-001', 'OP01', 'L', "
                "'Leader', 'FR', 'One Piece', 10.0, 'luffy.png')"
            )
            conn.execute("INSERT INTO purchases VALUES (1, 1, 2, 8.5, 'Near Mint')")
            conn.execute("INSERT INTO purchases VALUES (2, 1, 1, 12.0, 'Played')")
            conn.execute("INSERT INTO purchases VALUES (3, 2, 4, 1.5, 'Mint')")
            conn.commit()
        finally:
            conn.close()

    def colonnes_purchases(self):
        conn = sqlite3.connect(self.db_path)
        try:
            return {ligne[1] for ligne in conn.execute("PRAGMA table_info(purchases)")}
        finally:
            conn.close()

    def test_ancienne_base_na_pas_les_nouvelles_colonnes(self):
        self.creer_ancienne_base()
        self.assertNotIn("purchase_date", self.colonnes_purchases())
        self.assertNotIn("purchase_location", self.colonnes_purchases())

    def test_ouverture_ajoute_les_colonnes_manquantes(self):
        self.creer_ancienne_base()
        storage.get_connection().close()
        colonnes = self.colonnes_purchases()
        self.assertIn("purchase_date", colonnes)
        self.assertIn("purchase_location", colonnes)

    def test_anciens_achats_ont_une_date_none(self):
        self.creer_ancienne_base()
        for carte in storage.load_collection():
            for achat in carte.purchases:
                self.assertIsNone(achat.purchase_date)

    def test_anciens_achats_ont_un_lieu_none(self):
        self.creer_ancienne_base()
        for carte in storage.load_collection():
            for achat in carte.purchases:
                self.assertIsNone(achat.purchase_location)

    def test_donnees_existantes_restent_intactes(self):
        self.creer_ancienne_base()
        par_nom = {c.name: c for c in storage.load_collection()}
        self.assertEqual(set(par_nom), {"Trafalgar Law", "Luffy"})
        law = par_nom["Trafalgar Law"]
        self.assertEqual(
            (law.card_set_id, law.set, law.rarity, law.type, law.langue, law.tcg, law.market_price, law.card_image),
            ("OP10-119", "OP10", "SEC", "Personnage", "FR", "One Piece", 125.5, "law.png"),
        )
        self.assertEqual(
            [(a.quantity, a.purchase_price, a.condition) for a in law.purchases],
            [(2, 8.5, "Near Mint"), (1, 12.0, "Played")],
        )
        self.assertEqual(
            [(a.quantity, a.purchase_price, a.condition) for a in par_nom["Luffy"].purchases],
            [(4, 1.5, "Mint")],
        )

    def test_migration_est_idempotente(self):
        self.creer_ancienne_base()
        storage.get_connection().close()
        storage.get_connection().close()
        self.assertEqual(self.compter("purchases"), 3)
        self.assertEqual(len(storage.load_collection()), 2)

    def test_nouvel_achat_sur_base_migree_garde_date_et_lieu(self):
        self.creer_ancienne_base()
        luffy = storage.load_collection()[1]
        storage.add_purchase(luffy, Achat(1, 2.0, "Mint", "2026-05-05", "Salon"))
        achats = storage.load_collection()[1].purchases
        self.assertEqual(achats[-1], Achat(1, 2.0, "Mint", "2026-05-05", "Salon"))
        self.assertIsNone(achats[0].purchase_date)


if __name__ == "__main__":
    unittest.main()
