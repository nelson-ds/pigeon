import os
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import run

app = FastAPI()

origins = ["*"]
methods = ["*"]
headers = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=methods,
    allow_headers=headers
)


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "Coo!"}

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    run(app, host="0.0.0.0", port=port)
