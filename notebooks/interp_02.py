INTERP = {
"nettoyage": """**Lecture.** 4 843 voitures, sans doublon ni valeur manquante. Trois lignes impossibles sont retirées : un kilométrage négatif (-64 km), un autre à plus d'un million de km et une puissance de 0 ch. Il reste 4 840 voitures, louées de 10 à 422 € par jour (médiane 119 €).""",

"eda": """**Lecture.** Le prix monte avec la **puissance** (corrélation 0,63) et baisse avec le **kilométrage** (-0,45). Les options sont associées à des prix plus élevés : boîte automatique (+29 € en médiane), Getaround Connect (+20 €), GPS (+19 €), climatisation (+16 €). Les pneus hiver n'y changent rien (-3 €). Ce sont des écarts bruts : une voiture automatique est aussi souvent plus puissante, d'où l'intérêt d'un modèle qui combine toutes les variables.""",

"preparation": """**Lecture.** Le pipeline scikit-learn encode les 4 variables texte (one-hot ; les catégories de moins de 10 voitures, comme les marques rares, sont regroupées), standardise kilométrage et puissance et garde les 7 options en 0/1. Il est ajusté sur l'entraînement seulement (3 872 voitures), le test (968) sert à l'évaluation finale.

Chaque essai est enregistré dans **MLflow** (base `mlflow.db`) : modèle, hyperparamètres retenus, R² de validation croisée, R² et erreurs sur le test, durée, et le pipeline entraîné avec sa signature. L'interface `mlflow ui --backend-store-uri sqlite:///mlflow.db` permet de comparer les essais.""",

"resultats": """**Lecture.**

| Modèle | Réglage retenu | R² validation croisée | R² test | Erreur moyenne (MAE) test |
|---|---|---|---|---|
| Régression linéaire | – | 0,697 | 0,713 | 12,4 € |
| Ridge | alpha = 3 | 0,698 | 0,712 | 12,4 € |
| Forêt aléatoire | 300 arbres, profondeur 20 | 0,747 | 0,747 | 10,9 € |
| **Gradient boosting** | 300 itérations, taux 0,05, 31 feuilles | **0,762** | **0,771** | **10,6 €** |

Les modèles linéaires plafonnent à 0,71 : ils ne captent ni les effets non linéaires ni les interactions entre variables, ce que font les arbres. La forêt aléatoire surapprend nettement (R² de 0,97 en entraînement contre 0,75 en test) ; le gradient boosting est le meilleur en validation croisée comme en test, avec un écart plus raisonnable (0,90 contre 0,77).""",

"choix": """**Lecture.** Le gradient boosting est retenu sur le R² de validation croisée (le test n'a servi qu'à confirmer). Sur le test, l'erreur médiane est de 7 € par jour et 90 % des prix sont prédits à moins de 23 € près. Les erreurs se concentrent aux extrémités, où les données sont rares : les 92 voitures du test à 80 € ou moins sont surestimées de 23 € en moyenne (dont des prix de 10 €, probablement des erreurs de saisie), les 3 voitures au-delà de 250 € sous-estimées de 73 €. Entre 80 et 160 €, l'erreur moyenne n'est que de 8 €.""",

"importance": """**Lecture.** La **puissance** est de loin la variable la plus importante (mélanger ses valeurs fait perdre 0,53 de R²), devant le **kilométrage** (0,33) et la **marque** (0,10). Le type de voiture, le GPS et le carburant comptent un peu ; la couleur, le parking privé et les pneus hiver presque pas.""",

"final": """**Lecture.** Le modèle final reprend exactement les réglages choisis et est réentraîné sur les 4 840 voitures. Il est exporté dans `api/model.joblib` avec l'ordre des 13 variables, que l'API utilise pour construire ses entrées, et enregistré dans le registre de modèles MLflow sous le nom `getaround-pricing`. Sur les deux premières voitures : 109 € prédits pour 106 €, 263 € pour 264 €.""",

"conclusions": """- **Modèle retenu** : gradient boosting (HistGradientBoostingRegressor), R² 0,77 et erreur absolue moyenne de 10,6 € sur le test, pour un prix médian de 119 €.
- **Ce qui fait le prix** : la puissance, le kilométrage, puis la marque ; les options pèsent peu une fois ces variables connues.
- **Industrialisation** : essais suivis et modèle enregistré dans MLflow, modèle servi par l'API `/predict` (FastAPI), documentée sur `/docs`.

**Limites.** 4 840 voitures, très peu de voitures de luxe, pas de localisation ni de saison (deux facteurs de prix importants pour la location). **Pistes** : ajouter la ville et la période, réentraîner régulièrement et suivre dans MLflow la dérive des prix prédits par rapport aux prix réellement choisis.""",
}
