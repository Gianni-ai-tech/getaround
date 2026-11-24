"""Point d'entrée AWS Lambda : l'application FastAPI servie via une URL de fonction Lambda."""
from mangum import Mangum

from app import app

handler = Mangum(app, lifespan="off")
