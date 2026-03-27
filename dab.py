import threading
import time

from compte import Compte

class DAB:
  def __init__(self, nb_dab: int = 2):
    self.nb_dab = nb_dab
    self.__semaphore = threading.Semaphore(nb_dab)

  def retirer(self, compte: Compte, montant: float, nom_client: str) -> bool:
    print(f"[DAB] {nom_client} attend un DAB disponible...")

    with self.__semaphore:
      print(f"[DAB] {nom_client} utilise un DAB")
      time.sleep(0.5)
      success = compte.retirer(montant)

      if success:
        print(f"[DAB] {nom_client} a retiré {montant}€ (nouveau solde: {compte.get_solde()}€)")
      else:
        print(f"[DAB] {nom_client} - retrait refusé (demande : {montant}€, solde actuel : {compte.get_solde()}€)")
      print(f"[DAB] {nom_client} libère le DAB")
      return success