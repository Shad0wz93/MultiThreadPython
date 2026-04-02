import threading
from concurrent.futures import ThreadPoolExecutor

from dab import DAB
from historique import Historique


class Guichet():
    """
    Thread pour le guichet bancaire

    Cycle : demarrer() -> run() -> arreter() -> join()
    """

    def __init__(self, id_guichet: int, banque=None, dab: DAB = None, historique: Historique = None):
        """
        :param id_guichet: numéro du guichet (1, 2, 3,...)
        :param banque: instance de Banque pour les virements
        :param dab: instance de DAB (pour limiter les retraits concurrents)
        :param historique: instance de Historique (pour journaliser les opérations)
        """
        self.id_guichet = id_guichet
        self.name = f"Guichet-{id_guichet}"
        self.banque = banque
        self.dab = dab
        self.historique = historique

        self._clients_traites = 0
        self._lock_stats = threading.Lock()

    # -----------------
    # TRAITEMENT CLIENT
    # -----------------
    def traiter_client(self, client):
        """
        Traiter la demande du client - appelé par le pool dans un thread
        """

        print(f"[{self.name}] Prise en charge : {client.nom}")

        operation = client.operation
        compte = client.compte
        montant = client.montant

        try:
            if operation == "depot" and compte is not None:
                compte.deposer(montant)
                print(f"[{self.name}] fait un dépôt de {montant}€ -> solde : {compte.get_solde()}€")
                if self.historique:
                    self.historique.enregistrer("depot", str(compte.numero), float(montant), True)

            elif operation == "retrait" and compte is not None:
                # si DAB fourni, l'utiliser
                if self.dab:
                    possible = self.dab.retirer(compte, montant, client.nom)
                else:
                    possible = compte.retirer(montant)

                if possible:
                    print(f"[{self.name}] fait un retrait de {montant}€ -> solde : {compte.get_solde()}")
                else:
                    print(f"[{self.name}] se voit refusé un retrait de {montant}€ (solde insuffisant)")

                # historique (succès ou échec)
                if self.historique:
                    self.historique.enregistrer("retrait", str(compte.numero), float(montant), bool(possible))

            elif operation == "virement":
                if self.banque is not None and compte is not None and client.compte_destination is not None:
                    success = self.banque.virement(compte.numero, client.compte_destination.numero, montant)
                    if success:
                        print(f"[{self.name}] fait un virement de {montant}€ (#{compte.numero} -> #{client.compte_destination.numero})")
                    else:
                        print(f"[{self.name}] se voit refusé un virement de {montant}€ (solde insuffisant)")

                    if self.historique:
                        self.historique.enregistrer("virement", str(compte.numero), float(montant), bool(success))

            print(f"[{self.name}] {client.nom} -> traitement terminé !")

        except Exception as e:
            # critère 3 : isolation des erreurs
            print(f"[{self.name}] — client ignoré : {e}")

        finally:
            with self._lock_stats:
                self._clients_traites += 1

    @property
    def nb_clients_traites(self) -> int:
        with self._lock_stats:
            return self._clients_traites

# -----------------
# POOL DE GUICHETS
# -----------------

class PoolGuichets:
    """
    Gère N instance de guichets via un ThreadPoolExecutor
    Dispatch round-robin vers le prochain guichet.
    """

    def __init__(self, n_guichets: int, file_clients=None, banque=None, dab: DAB = None, historique: Historique = None):
        if n_guichets < 1:
            raise ValueError("Il faut au moins 1 guichet")

        self._guichets = [
            Guichet(i + 1, banque, dab=dab, historique=historique)
            for i in range(n_guichets)
        ]

        self._file_clients = file_clients

        self._executor = ThreadPoolExecutor(max_workers=n_guichets, thread_name_prefix="Guichet")
        self._futures : list = []
        self._index = 0
        self._lock_index = threading.Lock()

        print(f"[Pool] {n_guichets} guichet(s) prêts\n")

    def _prochain_guichet(self) -> Guichet:
        """
        Round-robin sur les guichets.
        """
        with self._lock_index:
            # le modulo distribue les clients cycliquements sur les N guichets
            g = self._guichets[self._index % len(self._guichets)]
            self._index =+ 1
            return g

    def soumettre(self, client):
        """
        Soumet un client au prochain guichet
        """
        guichet = self._prochain_guichet()

        def _tache():
            try:
                guichet.traiter_client(client)
            finally:
                if self._file_clients is not None:
                    self._file_clients.task_done()

        f = self._executor.submit(_tache)
        self._futures.append(f)

    def arreter(self):
        """
        Arrêt propre de tous les guichets dans le pool
        1. Signale l'arrêt à tous les guichets
        2. Attend (join) que chacun finisse son client en cours
        3. Ferme le pool
        """
        print("\n[Pool] Arrêt demandé — en attente de la fin des guichets…")

        self._executor.shutdown(wait=True)

        total = sum(g.nb_clients_traites for g in self._guichets)
        print(f"[Pool] Tous les guichets sont fermés — {total} client(s) traité(s) au total")