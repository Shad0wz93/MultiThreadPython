import threading
from queue import Queue, Full, Empty

class Client:
    def __init__(self, nom: str, operation: str = None, montant: float = None, compte=None, compte_destination=None):
        self.nom = nom
        self.operation = operation
        self.montant = montant
        self.compte = compte
        self.compte_destination = compte_destination

    def __str__(self):
        return f"Client: {self.nom}"

class FileClients:
    # File d'attente thread-safe. Queue pour FIFO, Lock pour les statistiques.
    
    def __init__(self, capacite_max: int = 10):
        self._file = Queue(maxsize=capacite_max)  # Queue thread-safe (blocage/réveil auto)
        self._clients_servis = 0
        self._clients_refuses = 0
        self._lock = threading.Lock()  # Protège les compteurs (opération += non-atomique)
    
    def rejoindre_file(self, client: Client, block: bool = False) -> bool:
        # Ajoute un client. Retourne False si file pleine (refus propre).
        try:
            self._file.put(client, block=block)  # Queue.put() déjà thread-safe
            print(f"{client.nom} a rejoint la file d'attente (position: {self.taille_file()})")
            return True
        except Full:
            with self._lock:  # Lock nécessaire car += pas atomique
                self._clients_refuses += 1
            print(f"{client.nom} refusé - file d'attente pleine ({self._file.maxsize} clients max)")
            return False
    
    def servir_client(self, timeout: float = None) -> Client:
        # Récupère le prochain client (FIFO). Bloque si vide, réveil auto au put().
        try:
            client = self._file.get(block=True, timeout=timeout)  # Bloque ici si file vide
        except Empty:
            return None  # Timeout dépassé

        with self._lock:  # Protège +=
            self._clients_servis += 1

        return client

    def task_done(self):
        # Indique que le traitement d'un client est terminé
        self._file.task_done()

    def join(self):
        # Bloque jusqu'à ce que tous les clients soient traités
        self._file.join()

    def taille_file(self) -> int:
        # Retourne le nombre de clients actuellement en attente (non traité).
        return self._file.qsize()
    
    def file_est_vide(self) -> bool:
        return self._file.empty()
    
    def file_est_pleine(self) -> bool:
        return self._file.full()
    
    def capacite_max(self) -> int:
        return self._file.maxsize