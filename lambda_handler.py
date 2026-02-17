"""
Lambda handler for Extraction Job API.
Mangum adapts FastAPI (ASGI) to AWS Lambda + API Gateway.
"""

from mangum import Mangum
from main import app

handler = Mangum(app, lifespan="off")
