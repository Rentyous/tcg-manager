"""Tests unitaires de collection.py.

collection.py persiste via storage.py : chaque test travaille sur une base
SQLite temporaire (storage.DB_PATH est redirigé), jamais sur collection.db.
"""

import tempfile
import unittest
from pathlib import Path

import collection
import storage
from models import Achat, Carte, get_quantity


def creer_carte(name="Trafalgar Law", card_set_id="OP10-119", rarity="SEC", langue="FR", achats=None):
    """Construit une Carte de test avec un premier achat (1 exemplaire) par défaut."""
    if achats is None:
        achats = [Achat(1, 10.0, "Near Mint", "2026-01-01", "Cardmarket")]
    return Carte(
        name=name,
        card_set_id=card_set_id,
        set="OP10",
        type="Personnage",
        rarity=rarity,
        langue=langue,
        tcg="One Piece",
        market_price=125.0,
        card_image="img.png",
        purchases=achats,
    )


class BaseTemporaire(unittest.TestCase):
    """Redirige storage.DB_PATH vers une base jetable, restaurée après chaque test."""

    def setUp(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        ancien_chemin = storage.DB_PATH
        self.addCleanup(setattr, storage, "DB_PATH", ancien_chemin)
        storage.DB_PATH = Path(dossier.name) / "test.db"


class TestAjouterCarte(BaseTemporaire):
    def test_nouvelle_carte_est_ajoutee_en_memoire(self):
        coll = []
        carte = creer_carte()
        resultat = collection.ajouter_carte(coll, carte)
        self.assertEqual(coll, [carte])
        self.assertIs(resultat, carte)

    def test_nouvelle_carte_est_persistee_en_base(self):
        collection.ajouter_carte([], creer_carte())
        rechargee = storage.load_collection()
        self.assertEqual(len(rechargee), 1)
        self.assertEqual(rechargee[0], creer_carte())

    def test_carte_existante_ne_cree_pas_de_doublon(self):
        coll = []
        collection.ajouter_carte(coll, creer_carte())
        collection.ajouter_carte(coll, creer_carte())
        self.assertEqual(len(coll), 1)

    def test_carte_existante_retourne_la_carte_deja_presente(self):
        coll = []
        premiere = collection.ajouter_carte(coll, creer_carte())
        resultat = collection.ajouter_carte(coll, creer_carte())
        self.assertIs(resultat, premiere)

    def test_carte_existante_cumule_les_achats_et_la_quantite(self):
        coll = []
        collection.ajouter_carte(coll, creer_carte(achats=[Achat(2, 8.0, "Mint")]))
        collection.ajouter_carte(coll, creer_carte(achats=[Achat(3, 9.0, "Played")]))
        self.assertEqual(len(coll[0].purchases), 2)
        self.assertEqual(get_quantity(coll[0]), 5)

    def test_carte_existante_avec_plusieurs_achats_les_rattache_tous(self):
        coll = []
        collection.ajouter_carte(coll, creer_carte(achats=[Achat(1, 8.0, "Mint")]))
        nouveaux = [Achat(2, 9.0, "Good"), Achat(4, 1.0, "Played")]
        collection.ajouter_carte(coll, creer_carte(achats=nouveaux))
        self.assertEqual(get_quantity(coll[0]), 7)

    def test_carte_existante_persiste_les_achats_cumules(self):
        coll = []
        collection.ajouter_carte(coll, creer_carte(achats=[Achat(2, 8.0, "Mint")]))
        collection.ajouter_carte(coll, creer_carte(achats=[Achat(3, 9.0, "Played")]))
        rechargee = storage.load_collection()
        self.assertEqual(len(rechargee), 1)
        self.assertEqual(get_quantity(rechargee[0]), 5)


class TestAjouterExemplaires(BaseTemporaire):
    def test_ajoute_un_achat_a_la_carte_en_memoire(self):
        coll = []
        carte = collection.ajouter_carte(coll, creer_carte())
        collection.ajouter_exemplaires(coll, carte, Achat(4, 7.0, "Good"))
        self.assertEqual(len(carte.purchases), 2)
        self.assertEqual(get_quantity(carte), 5)

    def test_ajoute_un_achat_en_base(self):
        coll = []
        carte = collection.ajouter_carte(coll, creer_carte())
        collection.ajouter_exemplaires(coll, carte, Achat(4, 7.0, "Good"))
        self.assertEqual(get_quantity(storage.load_collection()[0]), 5)

    def test_identifie_la_carte_par_get_id_et_modifie_celle_de_la_collection(self):
        coll = []
        existante = collection.ajouter_carte(coll, creer_carte())
        copie = creer_carte()
        resultat = collection.ajouter_exemplaires(coll, copie, Achat(2, 7.0, "Good"))
        self.assertIs(resultat, existante)
        self.assertEqual(get_quantity(existante), 3)

    def test_carte_absente_leve_value_error(self):
        with self.assertRaises(ValueError):
            collection.ajouter_exemplaires([], creer_carte(), Achat(1, 1.0, "Mint"))

    def test_carte_absente_ne_touche_pas_la_base(self):
        with self.assertRaises(ValueError):
            collection.ajouter_exemplaires([], creer_carte(), Achat(1, 1.0, "Mint"))
        self.assertEqual(storage.load_collection(), [])


class TestRechercherCarte(unittest.TestCase):
    def setUp(self):
        self.law = creer_carte(name="Trafalgar Law")
        self.luffy = creer_carte(name="Monkey D. Luffy", card_set_id="OP01-001")
        self.coll = [self.law, self.luffy]

    def test_recherche_partielle(self):
        self.assertEqual(collection.rechercher_carte(self.coll, "Traf"), [self.law])

    def test_recherche_insensible_a_la_casse(self):
        self.assertEqual(collection.rechercher_carte(self.coll, "lUfFy"), [self.luffy])

    def test_recherche_retourne_toutes_les_cartes_correspondantes(self):
        autre_law = creer_carte(name="Trafalgar Law", rarity="SR")
        self.coll.append(autre_law)
        self.assertEqual(collection.rechercher_carte(self.coll, "law"), [self.law, autre_law])

    def test_recherche_sans_resultat_retourne_liste_vide(self):
        self.assertEqual(collection.rechercher_carte(self.coll, "Zoro"), [])

    def test_recherche_dans_collection_vide(self):
        self.assertEqual(collection.rechercher_carte([], "Law"), [])


class TestFiltrerParRarete(unittest.TestCase):
    def setUp(self):
        self.sec = creer_carte(rarity="SEC")
        self.sr = creer_carte(rarity="SR")
        self.cartes = [self.sec, self.sr]

    def test_filtre_sur_la_rarete_exacte(self):
        self.assertEqual(collection.filtrer_par_rarete(self.cartes, "SR"), [self.sr])

    def test_filtre_insensible_a_la_casse(self):
        self.assertEqual(collection.filtrer_par_rarete(self.cartes, "sec"), [self.sec])

    def test_filtre_nest_pas_partiel(self):
        self.assertEqual(collection.filtrer_par_rarete(self.cartes, "S"), [])

    def test_filtre_sans_resultat_retourne_liste_vide(self):
        self.assertEqual(collection.filtrer_par_rarete(self.cartes, "C"), [])


class TestTrouverCarte(unittest.TestCase):
    def test_carte_trouvee(self):
        carte = creer_carte()
        resultat = collection.trouver_carte([carte], "Trafalgar Law", "OP10-119", "SEC", "FR")
        self.assertIs(resultat, carte)

    def test_carte_absente_retourne_none(self):
        resultat = collection.trouver_carte([creer_carte()], "Zoro", "OP01-025", "R", "FR")
        self.assertIsNone(resultat)

    def test_collection_vide_retourne_none(self):
        self.assertIsNone(collection.trouver_carte([], "Trafalgar Law", "OP10-119", "SEC", "FR"))

    def test_meme_nom_rarete_differente_reste_distincte(self):
        sec = creer_carte(rarity="SEC")
        sr = creer_carte(rarity="SR")
        coll = [sec, sr]
        self.assertIs(collection.trouver_carte(coll, "Trafalgar Law", "OP10-119", "SR", "FR"), sr)
        self.assertIs(collection.trouver_carte(coll, "Trafalgar Law", "OP10-119", "SEC", "FR"), sec)

    def test_meme_nom_langue_differente_reste_distincte(self):
        fr = creer_carte(langue="FR")
        en = creer_carte(langue="EN")
        coll = [fr, en]
        self.assertIs(collection.trouver_carte(coll, "Trafalgar Law", "OP10-119", "SEC", "EN"), en)
        self.assertIsNone(collection.trouver_carte(coll, "Trafalgar Law", "OP10-119", "SEC", "JP"))


class TestCartesDistinctesAjoutees(BaseTemporaire):
    def test_meme_nom_rarete_ou_langue_differente_ne_sont_pas_fusionnees(self):
        coll = []
        collection.ajouter_carte(coll, creer_carte(rarity="SEC"))
        collection.ajouter_carte(coll, creer_carte(rarity="SR"))
        collection.ajouter_carte(coll, creer_carte(rarity="SEC", langue="EN"))
        self.assertEqual(len(coll), 3)
        self.assertEqual(len(storage.load_collection()), 3)


class TestSupprimerCarte(BaseTemporaire):
    def test_carte_retiree_de_la_memoire(self):
        coll = []
        carte = collection.ajouter_carte(coll, creer_carte())
        collection.supprimer_carte(coll, carte)
        self.assertEqual(coll, [])

    def test_carte_retiree_de_la_base(self):
        coll = []
        carte = collection.ajouter_carte(coll, creer_carte())
        collection.ajouter_exemplaires(coll, carte, Achat(2, 7.0, "Good"))
        collection.supprimer_carte(coll, carte)
        self.assertEqual(storage.load_collection(), [])

    def test_ne_supprime_que_la_carte_visee(self):
        coll = []
        law = collection.ajouter_carte(coll, creer_carte())
        luffy = collection.ajouter_carte(coll, creer_carte(name="Monkey D. Luffy", card_set_id="OP01-001"))
        collection.supprimer_carte(coll, law)
        self.assertEqual(coll, [luffy])
        rechargee = storage.load_collection()
        self.assertEqual([c.name for c in rechargee], ["Monkey D. Luffy"])

    def test_identifie_la_carte_par_get_id(self):
        coll = []
        collection.ajouter_carte(coll, creer_carte())
        collection.supprimer_carte(coll, creer_carte())
        self.assertEqual(coll, [])
        self.assertEqual(storage.load_collection(), [])

    def test_carte_absente_leve_value_error(self):
        with self.assertRaises(ValueError):
            collection.supprimer_carte([], creer_carte())

    def test_carte_absente_laisse_la_collection_intacte(self):
        coll = []
        collection.ajouter_carte(coll, creer_carte())
        with self.assertRaises(ValueError):
            collection.supprimer_carte(coll, creer_carte(name="Zoro", card_set_id="OP01-025"))
        self.assertEqual(len(coll), 1)
        self.assertEqual(len(storage.load_collection()), 1)


if __name__ == "__main__":
    unittest.main()
