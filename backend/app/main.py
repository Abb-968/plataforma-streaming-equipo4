from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="API Plataforma de Streaming - Equipo 4",
    description="MVP SCRUM trazado a los subsistemas SS-01 a SS-08 del diseño RUP.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Salud"])
def root():
    return {"proyecto": "Plataforma Streaming Equipo 4", "estado": "activo"}

@app.get("/health", tags=["Salud"])
def health_check():
    return {"db": "ok", "redis": "ok", "api": "ok"}