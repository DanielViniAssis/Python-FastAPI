import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from WorkOutApi.routers import api_router

app = FastAPI(title="WorkOutApi")
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run('main:app', host='0.0.0.0', port=8000, log_level='info', reload=True)
