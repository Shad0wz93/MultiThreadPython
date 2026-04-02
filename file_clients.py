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
    def __init__(self, capacite_max: int = 10):
        self._file = Queue(maxsize=capacite_max)
        self._clients_servis = 0
        self._clients_refuses = 0
        self._lock = threading.Lock()
    
    def rejoindre_file(self, client: Client, block: bool = False) -> bool:
        try:
            self._file.put(client, block=block)
            print(f"{client.nom} a rejoint la file d'attente (position: {self.taille_file()})")
            return True
        except Full:
            with self._lock:
                self._clients_refuses += 1
            print(f"{client.nom} refusé - file d'attente pleine ({self._file.maxsize} clients max)")
            return False
    
    def servir_client(self, timeout: float = None) -> Client:
        try:
            client = self._file.get(block=True, timeout=timeout)
        except Empty:
            return None

        # Incrémenter le compteur servi après récupération
        with self._lock:
            self._clients_servis += 1

        return client

    def task_done(self):
        self._file.task_done()

    def join(self):
        self._file.join()

    def taille_file(self) -> int:
        return self._file.qsize()
    
    def file_est_vide(self) -> bool:
        return self._file.empty()
    
    def file_est_pleine(self) -> bool:
        return self._file.full()
    
    def capacite_max(self) -> int:
        return self._file.maxsize