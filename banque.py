from compte import Compte
from surveillance import Notification


class Banque:
    def __init__(self, notification: Notification):
        self._comptes: dict[int, Compte] = {}
        self._notification = notification

    def ajouter_compte(self, compte: Compte):
        self._comptes[compte.numero] = compte

    def virement(self, numero_source: int, numero_destination: int, montant: int, historique=None) -> bool:
        source = self._comptes[numero_source]
        destination = self._comptes[numero_destination]

        premier, second = sorted([source, destination], key=lambda c: c.numero)

        with premier._lock:
            with second._lock:
                if source._solde < montant:
                    self._notification.alerter(source.numero)
                    if historique:
                        historique.enregistrer("virement", source.numero, montant, succes=False)
                    return False
                
                source._solde -= montant
                destination._solde += montant
                
                if historique:
                    historique.enregistrer("virement", source.numero, montant, succes=True)
                return True