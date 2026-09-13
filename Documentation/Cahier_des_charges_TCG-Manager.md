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
* Calcul automatique de la quantité              



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

### Achat

``` python
{
    "quantity": 2,
    "purchase\_price": 8.5,
    "condition": "Near Mint"
}
```

`condition` décrit l'état physique des exemplaires de cet achat. Échelle standard TCG (de la meilleure à la moins bonne) :

* Mint (M)
* Near Mint (NM)
* Excellent (EX)
* Good (GD)
* Lightly Played (LP)
* Played (PL)
* Bad / Poor (PO)

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
└── collection.json
```



La structure peut changer, c'est celle que j'avais en tête me permettant de séparer les différentes couches d'architecture. Si tu trouves mieux tu peux modifier l'architecture du projet.

### Responsabilités

Module            Rôle

\---

`main.py`         Boucle principale et menu
`ui.py`           Interactions utilisateur
`collection.py`   Logique métier
`models.py`       Fonctions utilitaires (`get\_id`, `get\_quantity`)
`storage.py`      Sauvegarde / chargement

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
image          TEXT

### Table `purchases`

Champ            Type

\---

id               INTEGER PRIMARY KEY
card\_id          TEXT
quantity         INTEGER
purchase\_price   REAL
condition        TEXT

Relation :

&#x20;   cards (1)
       │
       └──────< purchases (N)


\---

## 6\. Menu utilisateur

``` text
===============================
      One Piece Manager
===============================

1 - Afficher la collection
2 - Ajouter une carte
3 - Rechercher une carte
4 - Quitter
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

