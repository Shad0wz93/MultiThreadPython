import time
from compte import Compte
from file_clients import FileClients, Client
from guichet import PoolGuichets
from surveillance import TableauDeBord


# Créer comptes
comptes = {
    1: Compte(1, 1000),
    2: Compte(2, 500),
    3: Compte(3, 200)
}

# Créer file et pool
file_clients = FileClients(capacite_max=10)
pool_guichets = PoolGuichets(n_guichets=2, file_clients=file_clients)

# Créer tableau de bord
tableau = TableauDeBord(file_clients, pool_guichets, comptes, intervalle=1)

tableau.start()

print("Test US-05 : Tableau de bord\n")

# Ajouter clients
for i in range(5):
    if i % 2 == 0:
        client = Client(f"Client-{i}", "depot", compte=comptes[1], montant=100)
    else:
        client = Client(f"Client-{i}", "retrait", compte=comptes[2], montant=50)

    pool_guichets.soumettre(client)
    time.sleep(0.5)

time.sleep(4)

pool_guichets.arreter()
tableau.arreter()
tableau.join()

print("\nTest terminé")