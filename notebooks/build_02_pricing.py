"""Construit 02_pricing_model.ipynb. Interprétations dans interp_02.py."""
import nbformat as nbf, importlib.util, os

INTERP = {}
if os.path.exists("interp_02.py"):
    spec = importlib.util.spec_from_file_location("i", "interp_02.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); INTERP = m.INTERP

nb = nbf.v4.new_notebook(); C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))
lecture = lambda k: md(INTERP.get(k, f"**Lecture.** _à rédiger ({k})_"))

md("""
# Getaround – Modèle de prix de location journalier (MLflow)

**Objectif.** Suggérer aux propriétaires un prix de location par jour à partir des caractéristiques de leur voiture (marque, kilométrage, puissance, carburant, options…). Le modèle retenu est servi par l'API `/predict`.

**Démarche.**
1. Nettoyage et exploration des 4 843 voitures
2. Pipeline scikit-learn (encodage, standardisation) et quatre modèles : régression linéaire, Ridge, forêt aléatoire, gradient boosting
3. **Suivi des expériences avec MLflow** : paramètres, métriques, modèle de chaque essai
4. Choix du modèle, réentraînement sur toutes les données et export pour l'API
""")

code("""
import os, time, warnings; warnings.filterwarnings("ignore")
os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"; os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
import numpy as np, pandas as pd, joblib
import matplotlib.pyplot as plt, seaborn as sns
import mlflow, mlflow.sklearn, sklearn
from mlflow.models import infer_signature
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score, KFold
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
sns.set_theme(style="whitegrid"); plt.rcParams["figure.dpi"] = 110
SEED = 42
print("scikit-learn", sklearn.__version__, "| MLflow", mlflow.__version__)

df = pd.read_csv("../data/get_around_pricing_project.csv").drop(columns="Unnamed: 0")
print(df.shape, "| doublons :", df.duplicated().sum(), "| manquants :", df.isna().sum().sum())
df.head()
""")

code("""
aberrants = (df.mileage < 0) | (df.mileage > 500_000) | (df.engine_power == 0)
print("Retirées :", df[aberrants][["model_key", "mileage", "engine_power", "rental_price_per_day"]].to_dict("records"))
df = df[~aberrants].reset_index(drop=True)
print(f"Reste {len(df):,} voitures | prix par jour : médiane {df.rental_price_per_day.median():.0f} €, "
      f"de {df.rental_price_per_day.min()} à {df.rental_price_per_day.max()} €")
""")
lecture("nettoyage")

md("## 1. Exploration")
code("""
fig, axes = plt.subplots(1, 3, figsize=(16, 4))
sns.histplot(df.rental_price_per_day, bins=50, ax=axes[0], color="#1f6f7d"); axes[0].set(title="Prix par jour (€)", xlabel="€")
sns.scatterplot(data=df.sample(1500, random_state=SEED), x="engine_power", y="rental_price_per_day", alpha=0.4, ax=axes[1])
axes[1].set(title="Prix et puissance", xlabel="puissance (ch)", ylabel="€ / jour")
sns.scatterplot(data=df.sample(1500, random_state=SEED), x="mileage", y="rental_price_per_day", alpha=0.4, ax=axes[2])
axes[2].set(title="Prix et kilométrage", xlabel="km", ylabel="€ / jour")
plt.tight_layout(); plt.show()

options = [c for c in df.columns if df[c].dtype == bool]
effet = pd.DataFrame({c: df.groupby(c).rental_price_per_day.median() for c in options}).T
effet.columns = ["sans (médiane €)", "avec (médiane €)"]
effet["écart €"] = effet["avec (médiane €)"] - effet["sans (médiane €)"]
print("Corrélation avec le prix :", df[["mileage", "engine_power", "rental_price_per_day"]].corr()["rental_price_per_day"].round(2).to_dict())
effet.sort_values("écart €", ascending=False)
""")
lecture("eda")

md("## 2. Préparation et suivi MLflow")
code("""
CIBLE = "rental_price_per_day"
CATEGORIELLES = ["model_key", "fuel", "paint_color", "car_type"]
NUMERIQUES = ["mileage", "engine_power"]
BOOLEENNES = options
FEATURES = ["model_key", "mileage", "engine_power", "fuel", "paint_color", "car_type"] + BOOLEENNES   # ordre attendu par l'API
print("Ordre des variables pour l'API :", FEATURES)

X, y = df[FEATURES], df[CIBLE]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED)
print(f"Entraînement {len(X_tr):,} / test {len(X_te):,}")

def preparation():
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=10, sparse_output=False), CATEGORIELLES),
        ("num", StandardScaler(), NUMERIQUES),
        ("bool", "passthrough", BOOLEENNES)])

mlflow.set_tracking_uri("sqlite:///../mlflow.db")
mlflow.set_experiment("getaround-pricing")
CV = KFold(5, shuffle=True, random_state=SEED)
resultats = []

def essai(nom, modele, grille=None):
    pipe = Pipeline([("prep", preparation()), ("modele", modele)])
    with mlflow.start_run(run_name=nom):
        t = time.time()
        if grille:
            pipe = GridSearchCV(pipe, grille, cv=CV, scoring="r2", n_jobs=-1).fit(X_tr, y_tr)
            mlflow.log_params({k.replace("modele__", ""): v for k, v in pipe.best_params_.items()})
            r2_cv = pipe.best_score_; pipe = pipe.best_estimator_
        else:
            pipe.fit(X_tr, y_tr); r2_cv = cross_val_score(pipe, X_tr, y_tr, cv=CV, scoring="r2").mean()
        p_tr, p_te = pipe.predict(X_tr), pipe.predict(X_te)
        m = {"r2_cv": r2_cv, "r2_train": r2_score(y_tr, p_tr), "r2_test": r2_score(y_te, p_te),
             "rmse_test": mean_squared_error(y_te, p_te) ** 0.5, "mae_test": mean_absolute_error(y_te, p_te),
             "duree_s": time.time() - t}
        mlflow.log_param("modele", type(modele).__name__)
        mlflow.log_metrics(m)
        mlflow.sklearn.log_model(pipe, name="model", signature=infer_signature(X_tr, p_tr), input_example=X_tr.head(2),
                                 serialization_format="cloudpickle")   # modèle créé par nous : cloudpickle plutôt que skops
        resultats.append({"modèle": nom, **m})
    return pipe
""")
lecture("preparation")

code("""
modeles = {
    "Régression linéaire": essai("Régression linéaire", LinearRegression()),
    "Ridge": essai("Ridge", Ridge(), {"modele__alpha": [0.1, 1, 3, 10, 30, 100]}),
    "Forêt aléatoire": essai("Forêt aléatoire", RandomForestRegressor(random_state=SEED, n_jobs=-1),
                             {"modele__n_estimators": [300], "modele__max_depth": [10, 20, None], "modele__min_samples_leaf": [1, 3, 5]}),
    "Gradient boosting": essai("Gradient boosting", HistGradientBoostingRegressor(random_state=SEED),
                               {"modele__learning_rate": [0.05, 0.1], "modele__max_iter": [300, 600], "modele__max_leaf_nodes": [15, 31], "modele__min_samples_leaf": [10, 20]}),
}
res = pd.DataFrame(resultats).set_index("modèle")
res.round(3)
""")
lecture("resultats")

code("""
# Les mêmes essais tels que MLflow les a enregistrés
runs = mlflow.search_runs(experiment_names=["getaround-pricing"], order_by=["metrics.r2_test DESC"])
runs[["tags.mlflow.runName", "params.modele", "metrics.r2_cv", "metrics.r2_test", "metrics.rmse_test", "metrics.mae_test"]].head(8).round(3)
""")

code("""
meilleur_nom = res.r2_cv.idxmax()
meilleur = modeles[meilleur_nom]
p = meilleur.predict(X_te)
fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
axes[0].scatter(y_te, p, alpha=0.35, s=12); axes[0].plot([0, 450], [0, 450], color="red", lw=1)
axes[0].set(title=f"{meilleur_nom} : prédit vs réel (test)", xlabel="prix réel (€ / jour)", ylabel="prix prédit (€ / jour)")
sns.histplot(p - y_te, bins=50, ax=axes[1], color="#1f6f7d"); axes[1].set(title="Erreurs sur le test (prédit - réel)", xlabel="€")
plt.tight_layout(); plt.show()
erreur = (p - y_te).abs()
print(f"Choisi sur le R² de validation croisée : {meilleur_nom}")
print(f"Erreur absolue sur le test : médiane {erreur.median():.1f} €, 90 % des voitures à moins de {erreur.quantile(0.9):.1f} €")
""")
lecture("choix")

code("""
from sklearn.inspection import permutation_importance
imp = permutation_importance(meilleur, X_te, y_te, n_repeats=5, random_state=SEED, scoring="r2")
imp = pd.Series(imp.importances_mean, index=FEATURES).sort_values()
fig, ax = plt.subplots(figsize=(8, 4.5)); imp.plot.barh(ax=ax, color="#1f6f7d")
ax.set(title="Importance par permutation (baisse du R² test)", xlabel="baisse du R²"); plt.tight_layout(); plt.show()
""")
lecture("importance")

md("## 3. Modèle final pour l'API")
code("""
final = Pipeline([("prep", preparation()), ("modele", meilleur.named_steps["modele"])]).fit(X, y)   # mêmes réglages, toutes les données
os.makedirs("../api", exist_ok=True)
joblib.dump({"pipeline": final, "features": FEATURES, "modele": meilleur_nom}, "../api/model.joblib")
with mlflow.start_run(run_name=f"{meilleur_nom} – final (toutes les données)"):
    mlflow.log_param("modele", type(final.named_steps["modele"]).__name__)
    mlflow.log_params({k: v for k, v in final.named_steps["modele"].get_params().items() if k in ("alpha", "learning_rate", "max_iter", "max_leaf_nodes", "min_samples_leaf", "max_depth", "n_estimators")})
    info = mlflow.sklearn.log_model(final, name="model", signature=infer_signature(X, final.predict(X)), input_example=X.head(2),
                                    serialization_format="cloudpickle", registered_model_name="getaround-pricing")
print("Modèle exporté vers api/model.joblib et enregistré dans le registre MLflow 'getaround-pricing'")

exemple = X.head(2).values.tolist()
print("Exemple d'entrée pour /predict :", {"input": exemple})
print("Prédiction :", final.predict(pd.DataFrame(exemple, columns=FEATURES)).round(0).tolist(), "| prix réels :", y.head(2).tolist())
""")
lecture("final")

md("## 4. Conclusions")
lecture("conclusions")

nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, "02_pricing_model.ipynb"); print("ok", len(C))
