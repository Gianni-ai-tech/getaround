---
title: Getaround Pricing API
emoji: 🚗
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# API Getaround – prix de location suggéré

`POST /predict` renvoie un prix de location par jour (€) pour une ou plusieurs voitures. Documentation : `/docs` ; documentation interactive : `/swagger`.

```bash
curl -i -H "Content-Type: application/json" -X POST \
  -d '{"input": [["Citroën", 140411, 100, "diesel", "black", "convertible", true, true, false, false, true, true, true]]}' \
  https://<space>.hf.space/predict
```

Projet Jedha (bloc 5, CDSD) – Gianni Murru.
