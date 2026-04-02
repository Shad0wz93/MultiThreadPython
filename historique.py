import threading
from datetime import datetime

class Historique():
    """
    Historique concurrent des opérations.
    """

    def __init__(self):
        self._operations: list[dict] = []
        self._lock = threading.Lock()

    # -----------------
    # ENREGISTREMENT
    # -----------------

    def enregistrer(self, type_op: str, numero_compte: str, montant: float, succes: bool = True):
        """
            Enregistre une opération de façon thread-safe.
            Critères [1] et [3] : horodatage + verrou garantit l'ordre d'insertion.
        """
        with self._lock:
            operation = {
                "horodatage": datetime.now(), #dans le verrou
                "type": type_op,
                "compte": str(numero_compte),
                "montant": montant,
                "succes": succes,
            }
            self._operations.append(operation)

    # ------------------------------------------------------------------
    # Lecture — critère [2] : copie défensive pour ne pas bloquer
    # ------------------------------------------------------------------

    def get_toutes(self) -> list[dict]:
        """Retourne une copie de toutes les opérations."""
        with self._lock:
            return list(self._operations)

    def get_par_compte(self, numero_compte: str) -> list[dict]:
        """Critère [4] : filtre par numéro de compte."""
        with self._lock:
            return [op for op in self._operations if op["compte"] == str(numero_compte)]

    def get_par_type(self, type_op: str) -> list[dict]:
        """Critère [4] : filtre par type d'opération (depot, retrait, virement)."""
        with self._lock:
            return [op for op in self._operations if op["type"] == type_op]

    def afficher(self):
        """Affiche toutes les opérations dans l'ordre chronologique."""
        for op in self.get_toutes():
            statut = "✓" if op["succes"] else "✗"
            print(f"  {statut} [{op['horodatage']}] {op['type']:10} | compte {op['compte']} | {op['montant']}€")