"""Point d'entrée de l'application : boucle principale et menu.

Cf. Cahier des charges §4 (Architecture logicielle) et §6 (Menu utilisateur).
"""

import collection
import storage
import ui


def main():
    """Boucle principale de l'application."""
    coll = storage.load_collection()
    if not coll:
        print("Collection vide, ajoutez votre première carte.")

    while True:
        ui.afficher_menu()
        choix = ui.demander_choix()

        if choix == "1":
            ui.afficher_liste_cartes(coll)
        elif choix == "2":
            name, card_set_id, rarity, langue = ui.saisir_identifiant_carte()
            existante = collection.trouver_carte(coll, name, card_set_id, rarity, langue)
            if existante is not None:
                print("Cette carte est déjà dans la collection, ajout d'un nouvel achat.")
                achat = ui.saisir_achat()
                collection.ajouter_exemplaires(coll, existante, achat)
            else:
                card = ui.saisir_details_carte(name, card_set_id, rarity, langue)
                collection.ajouter_carte(coll, card)
        elif choix == "3":
            nom = ui.demander_nom_recherche()
            resultats = collection.rechercher_carte(coll, nom)
            ui.afficher_liste_cartes(resultats)
        elif choix == "4":
            while True:
                nom = ui.demander_nom_recherche()
                if not nom.strip():
                    print("Suppression annulée.")
                    break
                resultats = collection.rechercher_carte(coll, nom)
                if not resultats:
                    print("Aucune carte trouvée.")
                    break
                if len(resultats) > 1:
                    print("Plusieurs cartes correspondent :")
                    ui.afficher_liste_cartes(resultats)
                    rarete = ui.demander_rarete_filtre()
                    if not rarete.strip():
                        print("Suppression annulée.")
                        break
                    resultats = collection.filtrer_par_rarete(resultats, rarete)
                    if not resultats:
                        print("Aucune carte ne correspond à cette rareté.")
                        continue
                    if len(resultats) > 1:
                        print("Toujours plusieurs cartes, affinez le nom.")
                        ui.afficher_liste_cartes(resultats)
                        continue
                if ui.demander_confirmation_suppression(resultats[0]):
                    collection.supprimer_carte(coll, resultats[0])
                    print("Carte supprimée.")
                else:
                    print("Suppression annulée.")
                break
        elif choix == "5":
            break


if __name__ == "__main__":
    main()
