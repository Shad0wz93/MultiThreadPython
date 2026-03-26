import threading

class Compte:
    def __init__(self, numero, solde_initial=0):
        self.numero = numero
        self._solde = solde_initial
        self._lock = threading.Lock()

    def deposer(self, montant):
        if montant <= 0:
            raise ValueError("Le montant doit être positif.")
        with self._lock:
            self._solde += montant

    def retirer(self, montant) -> bool:
        if montant <= 0:
            raise ValueError("Le montant doit être positif.")
        with self._lock:
            if self._solde >= montant:
                self._solde -= montant
                return True
            return False

    def get_solde(self) -> float:
        with self._lock:
            return self._solde