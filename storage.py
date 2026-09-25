"""Sauvegarde et chargement de la collection en base de données SQLite.

Cf. Cahier des charges §5 (Base de données) et §4 (Architecture logicielle).
"""

import sqlite3
from pathlib import Path

from models import Achat, Carte, get_id

DB_PATH = Path(__file__).resolve().parent / "collection.db"


def get_connection(db_path=None):
    """Ouvre (ou crée) le fichier de base SQLite et s'assure que le schéma existe.

    Retourne une connexion sqlite3 avec row_factory=sqlite3.Row (accès aux
    colonnes par nom) et les clés étrangères activées. L'appelant est
    responsable de fermer la connexion (conn.close()).
    """
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _create_tables(conn)
    return conn


def _create_tables(conn):
    """Crée les tables cards et purchases si elles n'existent pas déjà (§5)."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY,
            name TEXT,
            card_set_id TEXT,
            "set" TEXT,
            rarity TEXT,
            type TEXT,
            langue TEXT,
            tcg TEXT,
            market_price REAL,
            card_image TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY,
            card_id INTEGER,
            quantity INTEGER,
            purchase_price REAL,
            condition TEXT,
            purchase_date TEXT,
            purchase_location TEXT,
            FOREIGN KEY (card_id) REFERENCES cards(id)
        )
        """
    )
    # Migration : une base créée avant l'ajout de la date et du lieu d'achat n'a
    # pas ces colonnes (CREATE TABLE IF NOT EXISTS ne les ajoute pas). Les achats
    # existants gardent NULL, on n'invente pas de date pour eux.
    colonnes = {row["name"] for row in conn.execute("PRAGMA table_info(purchases)")}
    for colonne in ("purchase_date", "purchase_location"):
        if colonne not in colonnes:
            conn.execute(f"ALTER TABLE purchases ADD COLUMN {colonne} TEXT")
    conn.commit()


def _insert_purchase(conn, card_id, purchase):
    """Insère un achat lié à `card_id` (sans commit) et retourne le curseur."""
    return conn.execute(
        "INSERT INTO purchases (card_id, quantity, purchase_price, condition, purchase_date, purchase_location) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            card_id,
            purchase.quantity,
            purchase.purchase_price,
            purchase.condition,
            purchase.purchase_date,
            purchase.purchase_location,
        ),
    )


def load_collection():
    """Charge toute la collection depuis la base de données (§2.2).

    Ne prend aucun argument. Retourne une liste d'objets `Carte` (models.py),
    chacune avec sa liste `purchases` d'objets `Achat` reconstruite depuis la
    table purchases correspondante. Si la base n'existe pas encore ou est
    vide, retourne une liste vide (pas d'erreur).
    """
    conn = get_connection()
    try:
        card_rows = conn.execute("SELECT * FROM cards").fetchall()
        collection = []
        for row in card_rows:
            purchase_rows = conn.execute(
                "SELECT quantity, purchase_price, condition, purchase_date, purchase_location "
                "FROM purchases WHERE card_id = ?",
                (row["id"],),
            ).fetchall()
            purchases = [
                Achat(
                    quantity=p["quantity"],
                    purchase_price=p["purchase_price"],
                    condition=p["condition"],
                    purchase_date=p["purchase_date"],
                    purchase_location=p["purchase_location"],
                )
                for p in purchase_rows
            ]
            card = Carte(
                name=row["name"],
                card_set_id=row["card_set_id"],
                set=row["set"],
                rarity=row["rarity"],
                type=row["type"],
                langue=row["langue"],
                tcg=row["tcg"],
                market_price=row["market_price"],
                card_image=row["card_image"],
                purchases=purchases,
            )
            collection.append(card)
        return collection
    finally:
        conn.close()


def add_card(card):
    """Insère une nouvelle carte en base, avec ses achats déjà présents dans card.purchases.

    `card` : un objet `Carte` (models.py) qui n'existe pas encore en base
    (aucune vérification de doublon ici, c'est à l'appelant/collection.py de
    s'en assurer via get_id/rechercher_carte). Chaque `Achat` de
    card.purchases est inséré dans la table purchases, lié à la carte créée.
    Retourne l'id SQLite (INTEGER) de la carte insérée.
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO cards (name, card_set_id, "set", rarity, type, langue, tcg, market_price, card_image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                card.name,
                card.card_set_id,
                card.set,
                card.rarity,
                card.type,
                card.langue,
                card.tcg,
                card.market_price,
                card.card_image,
            ),
        )
        card_id = cur.lastrowid
        for purchase in card.purchases:
            _insert_purchase(conn, card_id, purchase)
        conn.commit()
        return card_id
    finally:
        conn.close()


def add_purchase(card, purchase):
    """Insère un nouvel achat pour une carte déjà présente en base.

    `card` : un objet `Carte` déjà existant en base ; il est retrouvé via
    get_id(card) (name, card_set_id, rarity, langue), pas via un id SQLite
    stocké côté Python (le modèle Carte n'en porte pas).
    `purchase` : un objet `Achat` à ajouter.
    Lève ValueError si aucune carte correspondante n'est trouvée en base.
    Retourne l'id SQLite (INTEGER) de l'achat inséré.
    """
    conn = get_connection()
    try:
        name, card_set_id, rarity, langue = get_id(card)
        row = conn.execute(
            "SELECT id FROM cards WHERE name = ? AND card_set_id = ? AND rarity = ? AND langue = ?",
            (name, card_set_id, rarity, langue),
        ).fetchone()
        if row is None:
            raise ValueError(f"Carte introuvable en base pour l'achat : {get_id(card)}")
        card_id = row["id"]
        cur = _insert_purchase(conn, card_id, purchase)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def delete_card(card):
    """Supprime une carte de la base, ainsi que tous ses achats.

    `card` : un objet `Carte` déjà existant en base ; il est retrouvé via
    get_id(card), comme add_purchase. Les lignes de purchases liées sont
    supprimées avant la ligne de cards (contrainte de clé étrangère,
    foreign_keys activées via PRAGMA), dans une seule transaction (un seul
    commit à la fin).
    Lève ValueError si aucune carte correspondante n'est trouvée en base.
    """
    conn = get_connection()
    try:
        name, card_set_id, rarity, langue = get_id(card)
        row = conn.execute(
            "SELECT id FROM cards WHERE name = ? AND card_set_id = ? AND rarity = ? AND langue = ?",
            (name, card_set_id, rarity, langue),
        ).fetchone()
        if row is None:
            raise ValueError(f"Carte introuvable en base pour la suppression : {get_id(card)}")
        card_id = row["id"]
        conn.execute("DELETE FROM purchases WHERE card_id = ?", (card_id,))
        conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        conn.commit()
    finally:
        conn.close()


def save_collection(collection):
    """Réécrit entièrement la base à partir d'une liste de `Carte`.

    Supprime toutes les lignes de purchases et cards puis les réinsère à
    partir de `collection`. Usage : resynchronisation complète (ex. import),
    pas pour persister un ajout unitaire — utiliser add_card/add_purchase
    pour ça, qui n'écrasent pas le reste de la base.
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM purchases")
        conn.execute("DELETE FROM cards")
        for card in collection:
            cur = conn.execute(
                """
                INSERT INTO cards (name, card_set_id, "set", rarity, type, langue, tcg, market_price, card_image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card.name,
                    card.card_set_id,
                    card.set,
                    card.rarity,
                    card.type,
                    card.langue,
                    card.tcg,
                    card.market_price,
                    card.card_image,
                ),
            )
            card_id = cur.lastrowid
            for purchase in card.purchases:
                _insert_purchase(conn, card_id, purchase)
        conn.commit()
    finally:
        conn.close()
