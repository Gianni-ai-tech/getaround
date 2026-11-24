# Getaround – délai entre locations et prix de location (déploiement)

Bloc 5 CDSD Jedha – Gianni Murru

## En ligne

| Livrable | Adresse |
|---|---|
| Dashboard (analyse des retards) | https://gianni2504-getaround-delay-dashboard.static.hf.space |
| API de prix – documentation | `https://2qdi4tfk6gyhjvqzmcomm54soe0ykjah.lambda-url.eu-west-3.on.aws/docs` |
| API de prix – prédiction | `POST https://2qdi4tfk6gyhjvqzmcomm54soe0ykjah.lambda-url.eu-west-3.on.aws/predict` |
| Code (ce dépôt) | https://github.com/Gianni-ai-tech/getaround |

```bash
curl -i -H "Content-Type: application/json" -X POST \
  -d '{"input": [["Citroën", 140411, 100, "diesel", "black", "convertible", true, true, false, false, true, true, true]]}' \
  https://2qdi4tfk6gyhjvqzmcomm54soe0ykjah.lambda-url.eu-west-3.on.aws/predict
# {"prediction":[108.9]}
```

## 1. Analyse des retards → dashboard

Question du Product Manager : quel délai minimum imposer entre deux locations d'une même voiture, et sur quel périmètre (toutes les voitures ou Connect seulement) ?

- 57,5 % des locations sont rendues en retard (médiane 9 min) ; Connect est plus ponctuel (43 % contre 61 % en Mobile).
- 218 des 1 729 locations consécutives sont **problématiques** (le conducteur suivant attend, 26 min en médiane) ; la location suivante est alors annulée dans 17,0 % des cas contre 11,2 %.
- **Recommandation : toutes les voitures, 60 à 90 minutes** : 67 à 79 % des cas problématiques évités pour 2,0 à 2,9 % du revenu touché (estimé par le nombre de locations). Connect seul ne peut pas éviter plus de 32 % des cas.

Notebook : `notebooks/01_delay_analysis.ipynb` · calculs partagés avec le dashboard : `dashboard/delay_lib.py`.

## 2. Modèle de prix → API

Prix de location journalier prédit à partir de 13 caractéristiques de la voiture (4 840 voitures). Essais suivis dans **MLflow** :

| Modèle | R² validation croisée | R² test | MAE test |
|---|---|---|---|
| Régression linéaire | 0,697 | 0,713 | 12,4 € |
| Ridge | 0,698 | 0,712 | 12,4 € |
| Forêt aléatoire | 0,747 | 0,747 | 10,9 € |
| **Gradient boosting (retenu)** | **0,762** | **0,771** | **10,6 €** |

Notebook : `notebooks/02_pricing_model.ipynb` · suivi : `mlflow ui --backend-store-uri sqlite:///mlflow.db` · modèle exporté : `api/model.joblib`, enregistré dans MLflow sous `getaround-pricing`.

## Arborescence

```
data/                      données Jedha (retards .xlsx, prix .csv)
notebooks/                 01 analyse des retards, 02 modèle de prix + MLflow (build_*.py + interp_*.py les génèrent)
dashboard/                 app Streamlit (app.py, delay_lib.py, rentals_data.csv) + Dockerfile
dashboard_static/          même app servie sans serveur avec stlite (Space Hugging Face « Static »)
api/                       API FastAPI : app.py, docs.html (/docs), model.joblib, Dockerfile
                           + lambda_handler.py, Dockerfile.lambda, deploy_lambda.sh (déploiement AWS Lambda)
mlflow.db                  suivi des essais MLflow (les artefacts mlruns/ ne sont pas versionnés : trop lourds)
```

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py                             # dashboard sur http://localhost:8501
cd api && uvicorn app:app --port 7860                      # API : http://localhost:7860/docs
```

## Hébergement

Les Spaces Hugging Face Docker étant devenus payants, le dashboard tourne dans un Space **Static** gratuit (Streamlit exécuté dans le navigateur avec stlite, premier chargement de 20 à 40 s) et l'API sur **AWS Lambda** (image Docker sur ECR, URL de fonction publique), déployée avec `api/deploy_lambda.sh` depuis AWS CloudShell. Les deux `Dockerfile` permettent aussi un hébergement Docker classique (Space Docker, Render…).
