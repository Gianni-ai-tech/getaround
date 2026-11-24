"""API Getaround : prix de location journalier suggéré pour une voiture."""
from pathlib import Path
from typing import Union

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

ICI = Path(__file__).parent
bundle = joblib.load(ICI / "model.joblib")
PIPELINE, FEATURES, NOM_MODELE = bundle["pipeline"], bundle["features"], bundle["modele"]
BOOLEENNES = FEATURES[6:]
NUMERIQUES = ["mileage", "engine_power"]
_encodeur = PIPELINE.named_steps["prep"].named_transformers_["cat"]
CATEGORIES = {nom: sorted(map(str, cats)) for nom, cats in zip(_encodeur.feature_names_in_, _encodeur.categories_)}

app = FastAPI(title="Getaround – prix de location", version="1.0.0",
              docs_url="/swagger", redoc_url=None,
              description="Suggère un prix de location par jour (€) à partir des caractéristiques d'une voiture.")


class Requete(BaseModel):
    input: list[list[Union[bool, int, float, str]]] = Field(
        ..., description="Une liste de voitures ; chaque voiture est une liste de 13 valeurs dans l'ordre de GET /features.",
        examples=[[["Citroën", 140411, 100, "diesel", "black", "convertible", True, True, False, False, True, True, True]]])


class Reponse(BaseModel):
    prediction: list[float] = Field(..., description="Prix suggéré par jour, en euros, dans l'ordre des voitures envoyées.")


def _booleen(v):
    if isinstance(v, str):
        if v.strip().lower() in ("true", "1", "yes", "oui"):
            return True
        if v.strip().lower() in ("false", "0", "no", "non"):
            return False
        raise ValueError(v)
    return bool(v)


def _tableau(lignes):
    for i, ligne in enumerate(lignes):
        if len(ligne) != len(FEATURES):
            raise HTTPException(422, f"Voiture n°{i} : {len(ligne)} valeurs reçues, {len(FEATURES)} attendues dans l'ordre {FEATURES}.")
    X = pd.DataFrame(lignes, columns=FEATURES)
    try:
        for c in NUMERIQUES:
            X[c] = X[c].astype(float)
        for c in BOOLEENNES:
            X[c] = X[c].map(_booleen)
    except (ValueError, TypeError) as e:
        raise HTTPException(422, f"Valeur invalide ({e}) : mileage et engine_power doivent être des nombres, les 7 options des booléens.")
    for c in CATEGORIES:
        X[c] = X[c].astype(str)
    return X


@app.post("/predict", response_model=Reponse, summary="Prix suggéré pour une ou plusieurs voitures")
def predict(requete: Requete):
    X = _tableau(requete.input)
    return {"prediction": [round(float(p), 2) for p in PIPELINE.predict(X)]}


@app.get("/features", summary="Ordre et valeurs attendues des 13 variables")
def features():
    return {"ordre": FEATURES, "numeriques": NUMERIQUES, "booleennes": BOOLEENNES,
            "categories_connues": CATEGORIES, "modele": NOM_MODELE}


@app.get("/health", summary="Vérifie que l'API répond")
def health():
    return {"status": "ok", "modele": NOM_MODELE}


@app.get("/", include_in_schema=False)
def accueil():
    return RedirectResponse("/docs")


@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
def documentation():
    return (ICI / "docs.html").read_text(encoding="utf-8")
