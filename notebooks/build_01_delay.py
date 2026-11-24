"""Construit 01_delay_analysis.ipynb. Interprétations dans interp_01.py."""
import nbformat as nbf, importlib.util, os

INTERP = {}
if os.path.exists("interp_01.py"):
    spec = importlib.util.spec_from_file_location("i", "interp_01.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); INTERP = m.INTERP

nb = nbf.v4.new_notebook(); C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))
lecture = lambda k: md(INTERP.get(k, f"**Lecture.** _à rédiger ({k})_"))

md("""
# Getaround – Analyse des retards au retour : quel délai minimum entre deux locations ?

**Problème.** Quand un conducteur rend la voiture en retard, le conducteur suivant attend, voire annule. Getaround veut imposer un **délai minimum** entre deux locations d'une même voiture : une voiture n'apparaît plus dans la recherche si le créneau demandé est trop proche d'une location déjà réservée.

**Le compromis.** Ce délai supprime des frictions mais bloque aussi des locations, donc du revenu. Le Product Manager doit choisir :
- le **seuil** : combien de minutes ?
- le **périmètre** : toutes les voitures, ou seulement les voitures *Connect* ?

**Questions traitées.** À quelle fréquence les conducteurs sont-ils en retard, et quel effet sur le suivant ? Combien de locations (et quelle part du revenu) seraient touchées selon le seuil et le périmètre ? Combien de cas problématiques seraient résolus ?

Les calculs sont dans `dashboard/delay_lib.py`, partagé avec le dashboard Streamlit pour que les deux donnent les mêmes chiffres.
""")

code("""
import sys; sys.path.insert(0, "../dashboard")
import numpy as np, pandas as pd
import matplotlib.pyplot as plt, seaborn as sns
from delay_lib import charger, impact, courbe, SCOPES
sns.set_theme(style="whitegrid"); plt.rcParams["figure.dpi"] = 110

loc, paires = charger("../data/get_around_delay_analysis.xlsx")
print(f"{len(loc):,} locations, {loc.car_id.nunique():,} voitures")
display(pd.crosstab(loc.checkin_type, loc.state, margins=True, margins_name="total"))
print("Valeurs manquantes :", loc.isna().sum()[lambda s: s > 0].to_dict())
""")
lecture("chargement")

md("## 1. À quelle fréquence les conducteurs rendent-ils la voiture en retard ?")
code("""
fin = loc[loc.state == "ended"]
retard = fin.delay_at_checkout_in_minutes.dropna()
print(f"Retard connu pour {len(retard):,} locations terminées sur {len(fin):,} ({fin.delay_at_checkout_in_minutes.isna().sum():,} sans mesure)")
print(f"En retard : {(retard > 0).mean():.1%} | retard médian : {retard.median():.0f} min | 90e centile : {retard.quantile(0.9):.0f} min | max : {retard.max():,.0f} min")

seuils = [0, 15, 30, 60, 120, 240, 720]
part = pd.DataFrame({t: [(fin[fin.checkin_type == t].delay_at_checkout_in_minutes.dropna() > s).mean() * 100 for s in seuils]
                     for t in ["mobile", "connect"]}, index=[f"> {s} min" for s in seuils])
part["toutes"] = [(retard > s).mean() * 100 for s in seuils]

fig, axes = plt.subplots(1, 2, figsize=(14, 4))
sns.histplot(data=fin.dropna(subset=["delay_at_checkout_in_minutes"]), x="delay_at_checkout_in_minutes", hue="checkin_type",
             binrange=(-300, 600), bins=60, stat="percent", common_norm=False, ax=axes[0])
axes[0].axvline(0, color="black", lw=1); axes[0].set(title="Retard au retour (zoom de -5 h à +10 h)", xlabel="minutes (négatif = en avance)")
part[["mobile", "connect"]].plot.bar(ax=axes[1], color=["#4c72b0", "#dd8452"], rot=0)
axes[1].set(title="Part des locations rendues avec plus de X minutes de retard", ylabel="%")
plt.tight_layout(); plt.show()
part.round(1)
""")
lecture("retards")

md("## 2. Locations consécutives : quand le retard gêne-t-il le conducteur suivant ?")
code("""
print(f"{len(paires):,} locations ont une location précédente sur la même voiture à moins de 12 h "
      f"({len(paires) / len(loc):.1%} des locations) ; retard précédent inconnu pour {paires.retard_precedent.isna().sum()}")
connus = paires.dropna(subset=["retard_precedent"])
print(f"Cas problématiques (retard du précédent > délai prévu) : {connus.probleme.sum()} sur {len(connus)} ({connus.probleme.mean():.1%})")
print("Attente du conducteur suivant dans ces cas (min) :", connus[connus.probleme].attente.describe(percentiles=[.5, .75, .9]).round(0).to_dict())

annul = connus.groupby("probleme").state.apply(lambda s: (s == "canceled").mean() * 100).rename({False: "retard absorbé", True: "conducteur suivant attend"})
fig, axes = plt.subplots(1, 2, figsize=(14, 4))
sns.histplot(paires.delai_prevu, bins=25, ax=axes[0], color="#1f6f7d")
axes[0].set(title="Délai prévu entre deux locations consécutives", xlabel="minutes (données limitées à 12 h)")
annul.plot.bar(ax=axes[1], color=["#8fb3d9", "#c44e52"], rot=0)
for c in axes[1].containers: axes[1].bar_label(c, fmt="%.1f %%")
axes[1].set_ylim(0, annul.max() * 1.2); axes[0].set_ylabel("nombre de locations")
axes[1].set(title="Taux d'annulation de la location suivante", ylabel="%", xlabel="")
plt.tight_layout(); plt.show()
print("Par type de check-in :")
connus.groupby("checkin_type").agg(paires=("probleme", "size"), cas_problematiques=("probleme", "sum"), part=("probleme", "mean")).round(3)
""")
lecture("paires")

md("""
## 3. Le compromis seuil × périmètre

Pour un seuil *S*, toute location dont le délai prévu avec la précédente est inférieur à *S* n'aurait pas pu être réservée. On compte :
- les **locations bloquées** (et, parmi elles, celles qui ont eu lieu : **proxy du revenu perdu**, faute de prix dans ces données) ;
- les **cas problématiques résolus** : ceux où le conducteur suivant a attendu et que le seuil aurait évités.
""")
code("""
c = courbe(loc, paires)
fig, axes = plt.subplots(1, 2, figsize=(14, 4.2))
for nom, g in c.groupby("périmètre", sort=False):
    axes[0].plot(g.seuil, g["% du revenu (proxy)"], marker="o", ms=3, label=nom)
    axes[1].plot(g.seuil, g["% de tous les cas problématiques"], marker="o", ms=3, label=nom)
axes[0].set(title="Revenu touché (% des locations terminées)", xlabel="seuil (minutes)", ylabel="%")
axes[1].set(title="Cas problématiques résolus (% des 218)", xlabel="seuil (minutes)", ylabel="%")
for ax in axes: ax.axvline(60, color="grey", ls=":"); ax.legend()
plt.tight_layout(); plt.show()

colonnes = ["locations bloquées", "% du revenu (proxy)", "cas résolus", "% de tous les cas problématiques"]
tableau = c[c.seuil.isin([30, 60, 90, 120, 180, 240])].set_index(["périmètre", "seuil"])[colonnes]
tableau.round(1)
""")
lecture("compromis")

code("""
# Efficacité : combien de locations faut-il bloquer pour éviter un cas problématique ?
c["locations bloquées par cas résolu"] = c["locations bloquées"] / c["cas résolus"].replace(0, np.nan)
c[c.seuil.isin([30, 60, 120, 240, 720])].pivot(index="seuil", columns="périmètre", values="locations bloquées par cas résolu").round(1)
""")
lecture("efficacite")

md("## 4. Recommandation")
lecture("recommandation")

nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, "01_delay_analysis.ipynb"); print("ok", len(C))
