"""
Mangum Handler for AWS Lambda / Serverless deployment
Converts FastAPI ASGI app to Lambda handler
"""
from mangum import Mangum
from backend.server import app

handler = Mangum(app)
