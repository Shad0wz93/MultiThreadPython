import threading

from dab import DAB
from historique import Historique


class Guichet(threading.Thread):
    """
    Thread pour le guichet bancaire

    Cycle : demarrer() -> run() -> arreter() -> join()
    """

    def __init__(self, id_guichet: int, file_clients, banque=None, dab: DAB = None, historique: Historique = None):
        """
        :param id_guichet: numéro du guichet (1, 2, 3,...)
        :param file_clients:
        :param banque: instance de Banque pour les virements
        :param dab: instance de DAB (pour limiter les retraits concurrents)
        :param historique: instance de Historique (pour journaliser les opérations)
        """
        super().__init__(name=f"Guichet-{id_guichet}", daemon=False)
        self.id_guichet = id_guichet
        self.file_clients = file_clients
        self.banque = banque
        self.dab = dab
        self.historique = historique

        self._stop_event = threading.Event()
        self._clients_traites = 0
        self._lock_stats = threading.Lock()

    # -----------------
    # BOUCLE PRINCIPALE
    # -----------------
    def run(self):
        print(f"[{self.name}] Guichet ouvert")

        while not self._stop_event.is_set():
            got_client = False

            try:
                client = self.file_clients.servir_client(timeout=1.0)
                if client is None:
                    continue

                got_client = True
                self._traiter_client(client)
            except Exception as e:
                # Isolation des erreurs : le guichet survit à n'importe quelle
                # exception levée pendant le traitement (US-03, critère 3)
                print(f"[{self.name}] — client ignoré : {e}")

            finally:
                # On ne fait task_done() QUE si on a réellement obtenu un client via get()
                if got_client:
                    self.file_clients.task_done()

        print(f"[{self.name}] Fermé — {self._clients_traites} client(s) traité(s)")

    # -----------------
    # TRAITEMENT CLIENT
    # -----------------
    def _traiter_client(self, client):
        """
        Traiter la demande du client
        """

        print(f"[{self.name}] Prise en charge : {client.nom}")

        operation = client.operation
        compte = client.compte
        montant = client.montant

        if operation == "depot" and compte is not None:
            compte.deposer(montant)
            print(f"[{self.name}] fait un dépôt de {montant}€ -> solde : {compte.get_solde()}€")
            if self.historique:
                self.historique.enregistrer("depot", str(compte.numero), float(montant), True)

        elif operation == "retrait" and compte is not None:
            # AJOUT MINIMAL: si DAB fourni, l'utiliser
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

                # AJOUT MINIMAL: historique
                if self.historique:
                    self.historique.enregistrer("virement", str(compte.numero), float(montant), bool(success))

        with self._lock_stats:
            self._clients_traites += 1

        print(f"[{self.name}] {client.nom} -> traitement terminé !")

    def arreter(self):
        """
        Demande d'arrêt du guichet
        """
        self._stop_event.set()

    @property
    def nb_clients_traites(self) -> int:
        with self._lock_stats:
            return self._clients_traites

# -----------------
# POOL DE GUICHETS
# -----------------

class PoolGuichets:
    """
    Créé et gère N guichets sur la même fil d'attente
    """

    def __init__(self, n_guichets: int, file_clients, banque=None, dab: DAB = None, historique: Historique = None):
        if n_guichets < 1:
            raise ValueError("Il faut au moins 1 guichet")

        self._guichets = [
            Guichet(i + 1, file_clients, banque, dab=dab, historique=historique)
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
            g.arreter() # sinon join bloque indéfiniment

        for g in self._guichets:
            g.join()

        total = sum(g.nb_clients_traites for g in self._guichets)
        print(f"[Pool] Tous les guichets sont fermés — {total} client(s) traité(s) au total")