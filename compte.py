import threading

class Compte:
    def __init__(self, numero, solde_initial=0):
        self.numero = numero
        self._solde = solde_initial
        self._lock = threading.Lock()

    def deposer(self, montant):
        with self._lock:
            self._solde += montant
            return True

    def retirer(self, montant) -> bool:
        with self._lock:
            if self._solde >= montant:
                self._solde -= montant
                return True
            return False

    def get_solde(self) -> float:
        with self._lock:
            return self._solde