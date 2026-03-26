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

        :param client:
        :return:
        """
