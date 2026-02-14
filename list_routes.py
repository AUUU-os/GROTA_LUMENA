import uvicorn
from corex.api_server import app
for route in app.routes:
    print(f"Route: {route.path} | Methods: {route.methods}")
