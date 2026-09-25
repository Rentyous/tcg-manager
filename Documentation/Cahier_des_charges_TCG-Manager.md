# Cahier des charges --- TCG Manager (MVP V1)

## 1\. Présentation du projet

**Nom du projet :** TCG Collection Manager

### Contexte

Développer une application en Python permettant de gérer une collection personnelle de cartes **de différents TCG**.

Le projet est développé selon une approche **MVP (Minimum Viable Product)** : les fonctionnalités essentielles sont réalisées en priorité.
avant les améliorations de confort (interface graphique, gestion avancée des erreurs, statistiques...).

L'ajout de cartes doit être fait manuellement car il n'existe pas d'API ou de base de donnée publique qui recense toutes les cartes de tous les TCG (Pokemon, One Piece, Riftbound, YuGiOh, Magic).

Cependant, une fois toutes les cartes que je recherche ou que je possède sont enregistrés, je peux créé une API qui se base sur ma base de données remplie.

### Objectifs

* Gérer une collection de cartes TCG.
* Conserver l'historique des achats de chaque carte.
* Sauvegarder durablement les données vers une base de donnée SQLite
* Structurer le projet comme une véritable application Python.

\---

## 2\. Fonctionnalités du MVP

### 2.1 Gestion de la collection

Fonctionnalité                                  

\---

* Afficher toute la collection                    
* Rechercher une carte par son nom                
* Ajouter une nouvelle carte                      
* Ajouter des exemplaires d'une carte existante   
* Supprimer une carte de la collection
* Calcul automatique de la quantité              

Précisions sur le comportement :

* **Ajout** : une seule entrée de menu couvre l'ajout d'une nouvelle carte et l'ajout d'exemplaires. L'utilisateur saisit d'abord les quatre champs qui identifient la carte (voir « Identité d'une carte », §3). Si la carte existe déjà, seul l'achat (quantité, prix, état, date, lieu) est demandé et il s'ajoute à la carte existante. Sinon, le reste des informations de la carte est demandé, suivi de son premier achat.
* **Recherche** : par nom, sur tout ou partie du nom, sans tenir compte de la casse.
* **Suppression** : la carte est recherchée par nom. Si plusieurs cartes correspondent, la rareté est demandée pour affiner. Une confirmation est demandée avant de supprimer la carte et tous ses achats.



### 2.2 Sauvegarde

* Chargement automatique de la collection au démarrage.
* Sauvegarde automatique en base de données lors de chaque action.

\---

## 3\. Modèle de données

### Carte

``` python
{
    "name": "Trafalgar Law",
    "card\_set\_id": "OP10-119",
    "set": "OP10",
    "rarity": "SEC",
    "type": "Personnage",

&#x20;   "langue": "FR",

&#x20;   "tcg": "Pokémon",
    "market\_price": 125,
    "card\_image": "...",
    "purchases": \[...]
}
```

**Identité d'une carte.** Deux cartes sont considérées comme la même carte si leur `name`, leur `card_set_id`, leur `rarity` et leur `langue` sont identiques (comparaison exacte). Une même impression en deux raretés ou en deux langues correspond donc à deux cartes distinctes, chacune avec son propre historique d'achats. Les autres champs (`set`, `type`, `tcg`, `market_price`, `card_image`) ne participent pas à cette comparaison.

### Achat

``` python
{
    "quantity": 2,
    "purchase\_price": 8.5,
    "condition": "Near Mint",
    "purchase\_date": "2026-09-25",
    "purchase\_location": "Cardmarket"
}
```

`purchase_date` est la date d'achat. Elle se saisit et s'affiche au format français `JJ-MM-AAAA` et vaut la date du jour par défaut lors de la saisie. En interne (modèle et base), elle est stockée au format ISO `AAAA-MM-JJ`, qui permet de trier les achats par ordre chronologique. Elle peut être vide pour les achats enregistrés avant l'ajout de ce champ.

`purchase_location` est le lieu d'achat (texte libre : boutique, site, événement...).

`condition` décrit l'état physique des exemplaires de cet achat. Échelle standard TCG (de la meilleure à la moins bonne) :

* Mint (M)
* Near Mint (NM)
* Excellent (EX)
* Good (GD)
* Lightly Played (LP)
* Played (PL)
* Bad (PO)

\---

## 4\. Architecture logicielle

### Structure actuelle

``` text
tcg-manager/
│
├── main.py
├── collection.py
├── models.py
├── storage.py
├── ui.py
├── requirements.txt
├── README.md
├── tests/
└── Documentation/
```

La base de données SQLite `collection.db` est créée automatiquement à la racine au premier lancement. Elle n'est pas versionnée (ignorée par Git) car elle contient les données réelles de la collection.



La structure peut changer, c'est celle que j'avais en tête me permettant de séparer les différentes couches d'architecture. Si tu trouves mieux tu peux modifier l'architecture du projet.

### Responsabilités

Module            Rôle

\---

`main.py`         Boucle principale et menu
`ui.py`           Interactions utilisateur
`collection.py`   Logique métier
`models.py`       Structures de données (`Carte`, `Achat`) et fonctions utilitaires (`get\_id`, `get\_quantity`)
`storage.py`      Sauvegarde / chargement (SQLite), création et migration du schéma
`tests/`          Tests unitaires (`unittest`)

\---

## 5\. Base de données

### Table `cards`

Champ          Type

\---

id             INTEGER PRIMARY KEY
name           TEXT
card\_set\_id    TEXT
set            TEXT
rarity         TEXT
type  	       TEXT

langue         TEXT

tcg            TEXT
market\_price   REAL
card\_image     TEXT

### Table `purchases`

Champ            Type

\---

id               INTEGER PRIMARY KEY
card\_id          INTEGER (clé étrangère vers cards.id)
quantity         INTEGER
purchase\_price   REAL
condition        TEXT
purchase\_date    TEXT (date ISO AAAA-MM-JJ)
purchase\_location TEXT

Relation :

&#x20;   cards (1)
       │
       └──────< purchases (N)


\---

## 6\. Menu utilisateur

``` text
===============================
        TCG Manager
===============================

1 - Afficher la collection
2 - Ajouter une carte
3 - Rechercher une carte
4 - Supprimer une carte
5 - Quitter
```

\---

## 7\. Contraintes techniques

### Langage

* Python 3.13+

### Bibliothèques

Bibliothèque   Utilité

\---
`sqlite3`      Base de données

\---

## 8\. Gestion des erreurs

### API

Gestion prévue :

* Carte introuvable (404)
* Erreur serveur (500)

### Utilisateur

Les validations de saisie sont volontairement **hors périmètre du MVP**,
l'application étant destinée à un usage personnel.

\---

## 9\. Intégration API 

Une fois l'application créé, je souhaite pouvoir taper en API dessus pour récupérer des information ou mettre a disposition les données de la base de données au format JSON en passant par des routes.



## 10\. Évolutions prévues (Backlog)

### Priorité haute

* \[ ] Affichage plus lisible de la collection
* \[ ] Choix de variante lorsqu'une carte possède plusieurs raretés
* \[ ] Interface graphique (Tkinter, Flet ou Web)

### Priorité moyenne

* \[ ] Statistiques de collection
* \[ ] Valeur totale de la collection
* \[ ] Prix moyen d'achat
* \[ ] Filtrer par extension ou rareté

### Long terme

* \[ ] API française personnelle
* \[ ] Import / export CSV
* \[ ] Gestion des decks

\---

## 11\. Critères de réussite

* \[x] Ajouter une carte via l'interface de l'application
* \[x] Rechercher une carte
* \[x] Gérer plusieurs versions d'une même carte
* \[x] Conserver plusieurs achats pour une carte
* \[x] Calculer la quantité totale
* \[x] Sauvegarder et recharger la collection
* \[x] Projet organisé en plusieurs modules Python

\---



**Version :** MVP V1

**Auteur :** Rentyous

**Prochaine étape :** Création d'un MVP et publication sur GitHub.

