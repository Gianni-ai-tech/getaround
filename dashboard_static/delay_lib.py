"""Calculs de l'analyse des retards Getaround, partagés par le notebook et le dashboard."""
import numpy as np
import pandas as pd

SCOPES = {"Toutes les voitures": None, "Connect seulement": "connect", "Mobile seulement": "mobile"}


def charger(chemin):
    """Charge les locations et construit les paires (location précédente → location suivante sur la même voiture)."""
    loc = pd.read_csv(chemin) if str(chemin).endswith(".csv") else pd.read_excel(chemin, sheet_name="rentals_data")
    prec = loc[["rental_id", "delay_at_checkout_in_minutes", "checkin_type"]].rename(columns={
        "rental_id": "previous_ended_rental_id", "delay_at_checkout_in_minutes": "retard_precedent",
        "checkin_type": "type_precedent"})
    paires = (loc[loc.previous_ended_rental_id.notna()]
              .merge(prec, on="previous_ended_rental_id", how="left")
              .rename(columns={"time_delta_with_previous_rental_in_minutes": "delai_prevu"}))
    # Attente du conducteur suivant : retard du précédent au-delà du délai prévu entre les deux locations
    paires["attente"] = paires.retard_precedent - paires.delai_prevu
    paires["probleme"] = paires.attente > 0
    return loc, paires


def impact(loc, paires, seuil, scope=None):
    """Effet d'un délai minimum `seuil` (minutes) appliqué au périmètre `scope` (None, 'connect' ou 'mobile')."""
    p = paires if scope is None else paires[paires.checkin_type == scope]
    bloquees = p[p.delai_prevu < seuil]                      # locations qui n'auraient pas pu être réservées
    connus = p.dropna(subset=["retard_precedent"])           # retard précédent connu
    return {
        "seuil": seuil,
        "locations bloquées": len(bloquees),
        "% des locations": len(bloquees) / len(loc) * 100,
        "locations terminées bloquées": int((bloquees.state == "ended").sum()),
        "% du revenu (proxy)": (bloquees.state == "ended").sum() / (loc.state == "ended").sum() * 100,
        "cas problématiques": int(connus.probleme.sum()),
        "cas résolus": int((connus.probleme & (connus.delai_prevu < seuil)).sum()),
        "% des cas résolus": (connus.probleme & (connus.delai_prevu < seuil)).sum() / max(1, connus.probleme.sum()) * 100,
        "% de tous les cas problématiques": (connus.probleme & (connus.delai_prevu < seuil)).sum()
                                            / paires.dropna(subset=["retard_precedent"]).probleme.sum() * 100,
    }


def courbe(loc, paires, seuils=range(0, 721, 30)):
    """Impact pour chaque seuil et chaque périmètre."""
    lignes = []
    for nom, scope in SCOPES.items():
        for s in seuils:
            lignes.append({"périmètre": nom, **impact(loc, paires, s, scope)})
    return pd.DataFrame(lignes)
