INTERP = {
"chargement": """**Lecture.** 21 310 locations sur 8 143 voitures. 80 % passent par le parcours *Mobile* (contrat signé sur le téléphone du propriétaire), 20 % par *Connect* (le conducteur ouvre la voiture avec son téléphone, sans rencontrer le propriétaire). 15 % des locations sont annulées, un peu plus en Connect (18,5 %) qu'en Mobile (14,5 %).

Valeurs manquantes : le retard au retour manque pour les 3 264 locations annulées sans mesure (logique) et pour 1 700 locations terminées. La location précédente n'est renseignée que si elle s'est terminée moins de 12 heures avant : c'est le cas de 1 841 locations seulement.""",

"retards": """**Lecture.** Plus de la moitié des locations (57,5 %) sont rendues en retard, mais souvent de peu : retard médian de 9 minutes. La queue est longue : 27 % ont plus d'une heure de retard, 3 % plus de 12 heures (quelques valeurs extrêmes jusqu'à 49 jours, probablement des oublis de check-out).

Les conducteurs **Connect sont nettement plus ponctuels** : 43 % en retard contre 61 % en Mobile, et 16 % contre 30 % au-delà d'une heure. En Mobile, le retour dépend du rendez-vous avec le propriétaire.""",

"paires": """**Lecture.** Le retard ne pose problème que si la voiture est relouée peu après. 1 841 locations (8,6 %) suivent une autre location de la même voiture à moins de 12 heures ; 279 sont même prévues **bout à bout** (délai de 0 minute).

Parmi les 1 729 paires dont le retard précédent est connu, **218 (12,6 %) sont problématiques** : le conducteur précédent rend la voiture après l'heure de départ prévue du suivant. L'attente médiane est de 26 minutes, et dépasse 80 minutes pour un quart des cas.

Effet sur le conducteur suivant : 17,0 % des locations suivantes sont annulées quand il doit attendre, contre 11,2 % sinon (+5,8 points). Les cas problématiques sont deux fois plus fréquents en Mobile (15,9 %) qu'en Connect (8,7 %).""",

"compromis": """**Lecture.** Un seuil bloque toute location prévue moins de *S* minutes après la précédente.

- **Toutes les voitures** : 60 minutes évitent 146 des 218 cas problématiques (67 %) en touchant 2,0 % du revenu ; 120 minutes en évitent 180 (83 %) pour 3,3 %. Au-delà, la courbe des cas évités plafonne (93 % à 240 minutes) alors que le revenu touché continue de monter.
- **Connect seulement** : le revenu touché est faible (0,9 % à 60 minutes), mais seuls 69 des 218 cas problématiques concernent des voitures Connect. Même avec 12 heures de délai, on n'en éviterait que 32 %.

Le revenu est estimé par la part des locations terminées bloquées : c'est une borne haute, car un conducteur bloqué peut choisir un autre créneau ou une autre voiture.""",

"efficacite": """**Lecture.** Le coût d'un cas évité, en locations bloquées, augmente avec le seuil : sur toutes les voitures, 2,4 locations bloquées par cas évité à 30 minutes, 2,7 à 60, 3,7 à 120 et 7,9 à 720. Le périmètre **Mobile** est le plus efficace (2,2 à 60 minutes), car c'est là que se concentrent les retards ; Connect seul est le moins efficace (3,8 à 60 minutes).""",

"recommandation": """| Option | Cas problématiques évités | Revenu touché (proxy) | Locations bloquées par cas évité |
|---|---|---|---|
| Toutes les voitures, 60 min | 146 / 218 (67 %) | 2,0 % | 2,7 |
| **Toutes les voitures, 90 min** | **172 / 218 (79 %)** | **2,9 %** | **3,4** |
| Toutes les voitures, 120 min | 180 / 218 (83 %) | 3,3 % | 3,7 |
| Connect seulement, 120 min | 59 / 218 (27 %) | 1,4 % | 5,0 |

**Recommandation : activer le délai sur toutes les voitures, entre 60 et 90 minutes.** C'est la zone où la courbe des cas évités est encore raide : au-delà de 120 minutes, chaque cas évité coûte de plus en plus de locations. Limiter la fonctionnalité aux voitures Connect protégerait le revenu mais laisserait de côté plus des deux tiers des problèmes, qui viennent des voitures Mobile.

**Limites.** Pas de prix dans ces données (revenu estimé par le nombre de locations), seules les locations à moins de 12 heures d'intervalle sont renseignées, et l'effet réel d'un blocage (report ou perte) est inconnu : à mesurer par un test A/B sur une partie des voitures avant de généraliser.""",
}
