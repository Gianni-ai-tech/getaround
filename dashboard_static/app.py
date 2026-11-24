"""Dashboard Getaround : quel délai minimum imposer entre deux locations ?"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from delay_lib import SCOPES, charger, courbe, impact

st.set_page_config(page_title="Getaround – délai entre locations", page_icon="🚗", layout="wide")
DONNEES = Path(__file__).parent / "rentals_data.csv"
def kpi(col, label, valeur, note=None):
    col.metric(label, valeur)
    if note:
        col.caption(note)


COULEURS = {"Toutes les voitures": "#1f6f7d", "Connect seulement": "#e07a2f", "Mobile seulement": "#8fb3d9"}


@st.cache_data
def donnees():
    loc, paires = charger(DONNEES)
    return loc, paires, courbe(loc, paires, range(0, 721, 15))


loc, paires, c = donnees()
fin = loc[loc.state == "ended"]
connus = paires.dropna(subset=["retard_precedent"])

st.title("Getaround – quel délai minimum entre deux locations ?")
st.caption("Données Getaround 2017 : 21 310 locations, 8 143 voitures. Les retards qui empêchent le conducteur suivant de partir à l'heure "
           "génèrent attente et annulations ; un délai minimum les évite, mais bloque aussi des locations.")

with st.sidebar:
    st.header("Paramètres de la fonctionnalité")
    seuil = st.slider("Délai minimum entre deux locations (minutes)", 0, 720, 60, step=15)
    perimetre = st.radio("Périmètre", list(SCOPES), index=0)
    st.markdown("---")
    st.markdown("**Hypothèses**\n- Une location bloquée est perdue (borne haute : le conducteur peut choisir un autre créneau ou une autre voiture).\n"
                "- Faute de prix dans ces données, le **revenu touché** est estimé par la part des locations terminées bloquées.\n"
                "- Un **cas problématique** : le retard du conducteur précédent dépasse le délai prévu entre les deux locations.")

r = impact(loc, paires, seuil, SCOPES[perimetre])
k1, k2, k3, k4 = st.columns(4)
kpi(k1, "Locations bloquées", f"{r['locations bloquées']:,}".replace(",", " "), f"{r['% des locations']:.1f} % des locations")
kpi(k2, "Revenu touché (proxy)", f"{r['% du revenu (proxy)']:.1f} %", f"{r['locations terminées bloquées']} locations terminées")
kpi(k3, "Cas problématiques évités", f"{r['cas résolus']} / {len(connus[connus.probleme])}",
          f"{r['% de tous les cas problématiques']:.0f} % de tous les cas")
kpi(k4, "Locations bloquées par cas évité", f"{r['locations bloquées'] / r['cas résolus']:.1f}" if r["cas résolus"] else "–",
          "plus c'est bas, plus le seuil est efficace")

ong1, ong2, ong3, ong4 = st.tabs(["Compromis seuil × périmètre", "Retards au retour", "Impact sur le conducteur suivant", "Tableau détaillé"])

with ong1:
    g1, g2 = st.columns(2)
    for col, mesure, titre in [(g1, "% du revenu (proxy)", "Revenu touché (% des locations terminées)"),
                               (g2, "% de tous les cas problématiques", f"Cas problématiques évités (% des {len(connus[connus.probleme])})")]:
        fig = px.line(c, x="seuil", y=mesure, color="périmètre", color_discrete_map=COULEURS, markers=True,
                      labels={"seuil": "délai minimum (minutes)", mesure: "%"}, title=titre)
        fig.add_vline(x=seuil, line_dash="dot", line_color="grey")
        fig.update_layout(legend_title_text="", height=380, margin=dict(t=50, b=10))
        col.plotly_chart(fig, use_container_width=True)
    st.info("**Lecture.** Sur toutes les voitures, un délai de 60 minutes évite 67 % des cas problématiques en touchant 2,0 % du revenu ; "
            "120 minutes en évitent 83 % pour 3,3 %. Limité aux voitures Connect, le délai ne peut pas éviter plus de 32 % des cas, "
            "car la majorité des cas problématiques concerne des voitures Mobile.")

with ong2:
    retard = fin.dropna(subset=["delay_at_checkout_in_minutes"])
    a, b, cc = st.columns(3)
    kpi(a, "Rendues en retard", f"{(retard.delay_at_checkout_in_minutes > 0).mean():.1%}")
    kpi(b, "Retard médian", f"{retard.delay_at_checkout_in_minutes.median():.0f} min")
    kpi(cc, "Plus d'une heure de retard", f"{(retard.delay_at_checkout_in_minutes > 60).mean():.1%}")
    fig = px.histogram(retard[retard.delay_at_checkout_in_minutes.between(-300, 600)], x="delay_at_checkout_in_minutes",
                       color="checkin_type", barmode="overlay", histnorm="percent", nbins=90, opacity=0.6,
                       labels={"delay_at_checkout_in_minutes": "retard au retour (minutes, négatif = en avance)", "checkin_type": "check-in"},
                       color_discrete_map={"mobile": "#1f6f7d", "connect": "#e07a2f"},
                       title="Distribution des retards (zoom de -5 h à +10 h)")
    fig.add_vline(x=0, line_color="black")
    st.plotly_chart(fig, use_container_width=True)
    part = (retard.assign(en_retard=retard.delay_at_checkout_in_minutes > 0)
            .groupby("checkin_type").en_retard.mean().mul(100).round(1).rename("% rendues en retard"))
    st.dataframe(part.to_frame().T, use_container_width=True)

with ong3:
    a, b, cc = st.columns(3)
    kpi(a, "Locations précédées d'une autre à moins de 12 h", f"{len(paires):,}".replace(",", " "), f"{len(paires) / len(loc):.1%} des locations")
    kpi(b, "Cas problématiques", f"{connus.probleme.sum()}", f"{connus.probleme.mean():.1%} des locations consécutives")
    kpi(cc, "Attente médiane du conducteur suivant", f"{connus[connus.probleme].attente.median():.0f} min")
    annul = (connus.groupby("probleme").state.apply(lambda s: (s == "canceled").mean() * 100)
             .rename({False: "retard absorbé", True: "conducteur suivant attend"}).reset_index())
    fig = px.bar(annul, x="probleme", y="state", text_auto=".1f", color="probleme",
                 color_discrete_sequence=["#8fb3d9", "#b23b35"], title="Taux d'annulation de la location suivante (%)",
                 labels={"probleme": "", "state": "% annulées"})
    fig.update_layout(showlegend=False, height=380)
    st.plotly_chart(fig, use_container_width=True)
    par_type = connus.groupby("checkin_type").agg(paires=("probleme", "size"), cas_problematiques=("probleme", "sum"))
    par_type["% problématiques"] = (par_type.cas_problematiques / par_type.paires * 100).round(1)
    st.dataframe(par_type, use_container_width=True)

with ong4:
    t = c[c.seuil.isin([0, 15, 30, 60, 90, 120, 180, 240, 360, 720])].copy()
    t["locations bloquées par cas évité"] = (t["locations bloquées"] / t["cas résolus"].replace(0, float("nan"))).round(1)
    st.dataframe(t.drop(columns=["cas problématiques"]).round(1), use_container_width=True, hide_index=True)
    st.download_button("Télécharger toutes les valeurs (CSV)", c.to_csv(index=False).encode("utf-8"), "getaround_seuils.csv", "text/csv")

st.markdown("---")
st.markdown("**Recommandation.** Activer le délai sur **toutes les voitures**, avec un seuil de **60 à 90 minutes** : "
            "67 à 79 % des cas problématiques évités pour 2,0 à 2,9 % du revenu touché. Au-delà de 120 minutes, chaque cas évité coûte de plus en plus de locations.")
