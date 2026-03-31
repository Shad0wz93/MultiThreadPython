import threading

from surveillance import Notification


class Compte:
    def __init__(self, numero, notification: Notification, solde_initial=0):
        self.numero = numero
        self._solde = solde_initial
        self._lock = threading.Lock()
        self._notification = notification

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
            self._notification.alerter(self.numero)
            return False

    def get_solde(self) -> float:
        with self._lock:
            return self._solde