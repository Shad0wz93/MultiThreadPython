import threading
import time

from file_clients import Client, FileClients


# =============================================================================
# TEST 1 : Ordre FIFO strict
# =============================================================================
file = FileClients(capacite_max=5)
    
# Ajouter des clients dans un ordre précis
clients_entrants = [
  Client("Alice"),
  Client("Bob"),
  Client("Charlie"),
  Client("Diana")
]
    
for client in clients_entrants:
    file.rejoindre_file(client)
    time.sleep(0.1)
    
print(f"\nFile d'attente: {file.taille_file()} clients")
    
# Servir les clients et vérifier l'ordre de sortie
print("\nPrendre les clients dans l'ordre:")
clients_sortants = []
while not file.file_est_vide():
    client = file.servir_client(timeout=1)
    if client:
      clients_sortants.append(client)
      print(f"→ Servi = {client}")
    
ordre_correct = all(
  clients_entrants[i].nom == clients_sortants[i].nom 
  for i in range(len(clients_entrants))
)    
print(f"\nOrdre correct: {ordre_correct}")


# =============================================================================
# TEST 2 : Réveil automatique d'un guichet bloqué
# =============================================================================
file2 = FileClients(capacite_max=3)
client_servi = []

def guichet_thread():
    # Thread guichet qui attend passivement un client
    print("\nGuichet en attente d'un client...")
    client = file2.servir_client(timeout=5)  # Bloque ici jusqu'à l'arrivée d'un client
    if client:
        client_servi.append(client)
        print(f"Guichet = {client} servi après réveil automatique")

guichet = threading.Thread(target=guichet_thread)
guichet.start()

time.sleep(2)  # Laisser le guichet se bloquer

# Ajouter un client → doit réveiller le guichet bloqué
print("Ajout d'un client à la file...")
nouveau_client = Client("Eve")
file2.rejoindre_file(nouveau_client)

guichet.join()
print(f"Guichet réveillé automatiquement: {len(client_servi) == 1}")


# =============================================================================
# TEST 3 : Refus propre si file pleine
# =============================================================================
file3 = FileClients(capacite_max=3)

for i in range(3):
  client = Client(f"\nClient{i+1}")
  file3.rejoindre_file(client, block=False)

print(f"File d'attente: {file3.taille_file()}/{file3.capacite_max()} (pleine)")

# Tentative d'ajout alors que la file est pleine
client_refuse = Client("Magie")
resultat = file3.rejoindre_file(client_refuse, block=False)
print(f"Client refusé : {not resultat}\n")


# =============================================================================
# TEST 4 : Taille accessible en temps réel (thread-safe)
# =============================================================================
file4 = FileClients(capacite_max=10)
tailles_observees = []

def ajouter_clients():
  # Thread qui ajoute des clients progressivement
  for i in range(5):
    client = Client(f"ClientA{i}")
    file4.rejoindre_file(client)
    time.sleep(0.1)
    
def observer_taille():
  # Thread qui observe la taille en parallèle
  for _ in range(10):
    taille = file4.taille_file()  # Lecture thread-safe
    tailles_observees.append(taille)
    time.sleep(0.05)

t1 = threading.Thread(target=ajouter_clients)
t2 = threading.Thread(target=observer_taille)
    
t1.start()
t2.start()
  
t1.join()
t2.join()
    
print(f"Tailles observées pendant l'ajout: {tailles_observees}")
print(f"Taille finale: {file4.taille_file()} clients")

