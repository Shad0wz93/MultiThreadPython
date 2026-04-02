import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from compte import Compte
from banque import Banque
from file_clients import FileClients, Client
from guichet import PoolGuichets
from dab import DAB
from historique import Historique
from surveillance import Notification, TableauDeBord

# Paramètres de simulation

N_CLIENTS        = 50
N_COMPTES        = 10
N_GUICHETS       = 5
N_DAB            = 3
SOLDE_INIT       = 1000
CAPACITE_FILE    = 30
INTERVALLE_TABLO = 3

notification = Notification()

stats_lock = threading.Lock()
nb_operations = 0          # dépôts + retraits réussis
total_depots = 0
total_retraits_ok = 0

def suivi_operations(type_op: str, montant: float, succes: bool):
    """Callback appelé par Compte après dépôt/retrait.

    :param type_op: "depot" ou "retrait"
    :param montant: montant de l'opération
    :param succes
    """
    global nb_operations, total_depots, total_retraits_ok

    if not succes:
        return

    #plusieurs threads peuvent appeler ce callback en même temps
    with stats_lock:
        nb_operations += 1
        if type_op == "depot":
            total_depots += montant
        elif type_op == "retrait":
            total_retraits_ok += montant

# Comptes avec callback
comptes = {
    i: Compte(i, notification, solde_initial=SOLDE_INIT, callback_op=suivi_operations)
    for i in range(N_COMPTES)
}

banque = Banque(notification)
for c in comptes.values():
    banque.ajouter_compte(c)

file_clients  = FileClients(capacite_max=CAPACITE_FILE)
dab           = DAB(nb_dab=N_DAB)
historique    = Historique()

pool_guichets = PoolGuichets(
    n_guichets=N_GUICHETS,
    file_clients=file_clients,
    banque=banque,
    dab=dab,
    historique=historique
)

tableau = TableauDeBord(file_clients, pool_guichets, comptes, intervalle=INTERVALLE_TABLO)

def simuler_client(client_id: int):
    """Simule un client
    :param client_id: identifiant unique du client simulé
    :return: nombre d'opérations générées
    """
    nom = f"Client-{client_id:02d}"
    nb_ops = random.randint(1, 10)

    for _ in range(nb_ops):
        operation = random.choice(["depot", "retrait", "virement"])
        compte = random.choice(list(comptes.values()))
        montant = random.randint(10, 200)

        # Pour un virement, on choisit un compte destination différent
        destination = None
        if operation == "virement":
            destination = random.choice(list(comptes.values()))
            if destination.numero == compte.numero:
                continue  # on évite virement vers soi-même

        # Requête client = "ce que le guichet devra exécuter"
        client = Client(
            nom=nom,
            operation=operation,
            montant=montant,
            compte=compte,
            compte_destination=destination
        )

        # Ajout dans la file : si la file est bornée, l'appel peut bloquer temporairement
        file_clients.rejoindre_file(client)

        # Petite pause pour rendre la charge plus réaliste (arrivées non simultanées)
        time.sleep(random.uniform(0.05, 0.2))

    return nb_ops

def lancer_surveillance_decouvert():
    t = threading.Thread(
        target=notification.surveiller,
        daemon=True,
        name="Surveillance-Solde-Insuffisant"
    )
    t.start()
    return t

def main():
    print("\n" + "=" * 50)
    print("   BankThread — Simulation de charge (US-09)")
    print("=" * 50)
    print(f"  Clients   : {N_CLIENTS}")
    print(f"  Comptes   : {N_COMPTES}")
    print(f"  Guichets  : {N_GUICHETS}")
    print(f"  DAB       : {N_DAB}")
    print("=" * 50 + "\n")

    #référence pour le calcul du solde attendu
    solde_initial_total = sum(c.get_solde() for c in comptes.values())
    print(f"  Solde total initial : {solde_initial_total}€\n")

    # Démarrage des composants
    lancer_surveillance_decouvert()
    pool_guichets.demarrer()
    tableau.start()

    # Simulation
    print("  Simulation en cours...\n")
    debut = time.time()
    with ThreadPoolExecutor(max_workers=N_CLIENTS) as pool:
        futures = [pool.submit(simuler_client, i) for i in range(N_CLIENTS)]

        # Permet de récupérer les exceptions éventuelles des threads clients
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"  [Erreur] {e}")

    # attendre que tous les clients pris par les guichets soient traités
    file_clients.join()

    duree = time.time() - debut

    # Arrêt propre
    pool_guichets.arreter()
    tableau.arreter()
    tableau.join()

    # Résultats finaux
    solde_final_total = sum(c.get_solde() for c in comptes.values())
    with stats_lock:
        ops = nb_operations
        solde_attendu = solde_initial_total + total_depots - total_retraits_ok

    debit = ops / duree if duree > 0 else 0

    print("\n" + "=" * 50)
    print("   Résultats")
    print("=" * 50)
    print(f"  Opérations : {ops}")
    print(f"  Durée      : {duree:.2f}s")
    print(f"  Débit      : {debit:.1f} ops/seconde")
    print(f"  Solde attendu : {solde_attendu}€")
    print(f"  Solde final   : {solde_final_total}€")
    print("-" * 50)

    if solde_final_total == solde_attendu:
        print("  OK — aucune race condition")
    else:
        diff = solde_final_total - solde_attendu
        print(f"  ERREUR — Ecart de {diff}€ detecte (race condition !)")

    print("=" * 50 + "\n")

    print("Historique des opérations :")
    historique.afficher()

if __name__ == "__main__":
    main()