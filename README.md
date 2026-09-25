# TCG Manager

TCG Manager est un gestionnaire de collection de cartes à collectionner (TCG), multi-jeux, avec l'historique des achats de chaque carte. Les données sont stockées dans une base SQLite et l'application est un programme console écrit en Python.

C'est un outil à usage personnel. La saisie des cartes est manuelle : il n'existe pas de base publique recensant toutes les cartes de tous les TCG, et l'application n'en utilise aucune.

## Fonctionnalités

Le menu propose cinq actions :

1. **Afficher la collection** : liste toutes les cartes avec leurs informations, leur quantité totale et le détail de leurs achats.
2. **Ajouter une carte** : ajoute une nouvelle carte ou un nouvel achat sur une carte déjà possédée.
3. **Rechercher une carte** : recherche par nom (le texte saisi peut n'être qu'un extrait du nom, sans tenir compte de la casse).
4. **Supprimer une carte** : recherche la carte par nom, l'affiche puis demande une confirmation (`o`/`n`) avant de la supprimer.
5. **Quitter**.

Points de comportement à connaître :

- Une carte est identifiée par le quadruplet (nom, identifiant de set, rareté, langue). Deux impressions différentes d'une même carte sont donc deux cartes distinctes.
- À l'ajout, ces quatre champs sont demandés en premier. Si la carte est déjà dans la collection, seule la saisie de l'achat est demandée et il s'ajoute à la carte existante. Sinon, le reste des informations est demandé (set, type, TCG, prix du marché, image), suivi du premier achat.
- Chaque achat comporte une quantité, un prix, un état, une date d'achat et un lieu d'achat.
  - L'état est saisi librement. L'échelle proposée est : Mint, Near Mint, Excellent, Good, Lightly Played, Played, Bad.
  - La date se saisit et s'affiche au format `JJ-MM-AAAA`. Si la saisie est laissée vide, la date du jour est utilisée.
- La quantité totale d'une carte est la somme des quantités de ses achats.
- Si plusieurs cartes correspondent au nom lors d'une suppression, la rareté est demandée pour affiner la recherche. Une saisie vide annule la suppression.
- Supprimer une carte supprime aussi tous ses achats.
- Chaque ajout ou suppression est enregistré immédiatement en base, et la collection est rechargée au lancement.
- Les saisies ne sont pas validées : une quantité, un prix ou une date au mauvais format interrompt le programme avec une erreur.

## Prérequis et installation

- Python 3.13 ou plus récent.
- Aucune dépendance externe : seule la bibliothèque standard est utilisée (dont `sqlite3`). Le fichier `requirements.txt` ne liste aucun paquet.

Cloner le dépôt :

```bash
git clone https://github.com/Rentyous/tcg-manager.git
cd tcg-manager
```

Un environnement virtuel est optionnel, puisqu'il n'y a rien à installer. Pour en créer un malgré tout :

Windows (PowerShell) :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux / macOS :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Utilisation

Depuis la racine du projet :

```bash
python main.py
```

Le menu s'affiche, puis l'application attend le numéro de l'action à effectuer :

```text
===============================
      TCG Manager
===============================

1 - Afficher la collection
2 - Ajouter une carte
3 - Rechercher une carte
4 - Supprimer une carte
5 - Quitter
Choix :
```

Le menu est réaffiché après chaque action, jusqu'au choix de `5`.

## Données

- La base `collection.db` est créée automatiquement à la racine du projet au premier lancement.
- Elle est ignorée par Git (`.gitignore`) : elle contient vos données réelles et n'est jamais versionnée. Pour la sauvegarder, copiez simplement le fichier `collection.db` à l'abri.
- Les bases créées avant l'ajout de la date et du lieu d'achat sont migrées automatiquement au lancement. Les anciens achats gardent alors une date et un lieu non renseignés.

## Tests

Les tests utilisent le module `unittest` de la bibliothèque standard (72 tests). Depuis la racine du projet :

```bash
python -m unittest discover -s tests -t .
```

Chaque test travaille sur une base SQLite temporaire : `collection.db` n'est jamais lu ni modifié par les tests.

## Structure du projet

```text
.
├── main.py             Point d'entrée : boucle principale et menu
├── ui.py               Interactions utilisateur : saisies et affichage
├── collection.py       Logique métier : recherche, ajout, suppression
├── models.py           Structures de données (Carte, Achat) et utilitaires (get_id, get_quantity)
├── storage.py          Sauvegarde et chargement SQLite, création et migration du schéma
├── requirements.txt    Aucune dépendance externe
├── tests/              Tests unittest (models, storage, collection)
└── Documentation/      Cahier des charges
```

## Documentation et évolutions

Le cahier des charges et le backlog se trouvent dans [Documentation/Cahier_des_charges_TCG-Manager.md](Documentation/Cahier_des_charges_TCG-Manager.md).

Une API JSON exposant les données de la collection est prévue (section 9 du cahier des charges) mais n'est pas encore implémentée : le projet ne fournit aujourd'hui que l'application console.
