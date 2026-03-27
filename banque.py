from compte import Compte


class Banque:
    def __init__(self):
        self._comptes: dict[int, Compte] = {}

    def ajouter_compte(self, compte: Compte):
        self._comptes[compte.numero] = compte

    def virement(self, numero_source: int, numero_destination: int, montant: int) -> bool:
        source = self._comptes[numero_source]
        destination = self._comptes[numero_destination]

        premier, second = sorted([source, destination], key=lambda c: c.numero)

        with premier._lock:
            with second._lock:
                if source._solde < montant:
                    return False
                source._solde -= montant
                destination._solde += montant
                return True