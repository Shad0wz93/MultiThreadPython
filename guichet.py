import threading
import time
import random
from queue import Empty

class Guichet (threading.Thread):
    """
    Thread pour le guichet bancaire

    Cycle : demarrer() -> run() -> arreter() -> join()
    """

    def __init__(self, id_guichet: int, file_clients):
        """
        :param id_guichet: numéro du guichet (1, 2, 3,...)
        :param file_clients:
        """
        self.id_guichet = id_guichet
        self.file_clients = file_clients
        self._stop_event = threading.Event()
        self._clients_traites = 0
        self._lock_stats = threading.Lock()

    # -----------------
    # BOUCLE PRINCIPALE
    # -----------------
    def run(self):
        print(f"[{self.name}] Guichet ouvert")

        while self._actif:
            try:
                # si la file est vide, on reboucle 1s jusqu'à l'attente d'un client
                client = self._file.get(timeout=1.0)
            except Empty:
                # Pas de client dans la seconde écoulée → on vérifie _actif
                continue

            try:
                self._traiter_client(client)
            except Exception as e:
                # Isolation des erreurs : le guichet survit à n'importe quelle
                # exception levée pendant le traitement (US-03, critère 3)
                print(f"[{self.name}] — client ignoré : {e}")
            finally:
                self._file.task_done()

        print(f"[{self.name}] Fermé — {self._clients_traites} client(s) traité(s)")

    # -----------------
    # TRAITEMENT CLIENT
    # -----------------
    def _traiter_client(self, client):
        """
        Traiter la demande du client
        """

        print(f"[Prise en charge : {client}")

        operation = client.get("operation", "inconnu")
        compte = client.get("compte", None)
        montant = client.get("montant", 0)

        if operation == "depot" and compte is not None:
            compte.deposer(montant)
            print(f"[{self.name}] fait un dépôt de {montant}€ -> solde : {compte.get_solde()}€")

        elif operation == "retrait" and compte is not None:
            possible = compte.retraiter(montant)
            if possible:
                print(f"[{self.name}] fait un retrait de {montant}€ -> solde : {compte.get_solde()}")
            else:
                print(f"[{self.name}] se voit refusé un retrait de {montant}€ (solde insuffisant)")


        with self._lock_stats():
            self._clients_traites += 1

        print(f"[{self.name}] {client.get('nom', client)} -> traitement terminé !")

    def arreter(self):
        """
        Demande d'arrêt du guichet
        """
        self._stop_event.set()

# -----------------
# POOL DE GUICHETS
# -----------------

class PoolGuichets:
    """
    Créé et gère N guichets sur la même fil d'attente
    """

    def __init__(self, n_guichets: int, file_clients):
        """
        :param n_guichet: nombre de guichet dans le pool
        :param file_clients: file partagée de clients
        """
        if n_guichets < 1:
            raise ValueError("Il faut au moins 1 guichet")

        self._guichets = [
            Guichet(i + 1, file_clients)
            for i in range(n_guichets)
        ]

    def demarrer(self):
        """
        Démarrer tous les threads guichet dans le pool
        """
        for g in self._guichets:
            g.start()
        print(f"[Pool] {len(self._guichets)} guichet(s) démarrés\n")

    def arreter(self):
        """
        Arrêt propre de tous les guichets dans le pool
        1. Signale l'arrêt à tous les guichets
        2. Attend (join) que chacun finisse son client en cours
        """
        print("\n[Pool] Arrêt demandé — en attente de la fin des guichets…")

        for g in self._guichets:
            g.join()

        total = sum(g.nb_clients_traites for g in self._guichets)
        print(f"[Pool] Tous les guichets sont fermés — {total} client(s) traité(s) au total")