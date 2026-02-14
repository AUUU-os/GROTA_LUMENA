import uvicorn
import os
import sys
sys.path.append(r"E:\SHAD\GROTA_LUMENA\CORE")
from corex.api_server import app
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)
