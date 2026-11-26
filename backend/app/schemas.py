from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class RegistroRequest(BaseModel):
    correo: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    pais_iso: str = Field(default="MX", min_length=2, max_length=2)
    nombre_perfil_titular: str = Field(..., min_length=2, max_length=50)
    fecha_nacimiento: date = Field(default=date(2000, 1, 1))


class LoginRequest(BaseModel):
    correo: EmailStr
    password: str = Field(..., min_length=1, max_length=72)


class PerfilResumen(BaseModel):
    id: UUID
    nombre: str
    clasificacion_maxima: str
    es_titular: bool
    tiene_nip: bool

    class Config:
        from_attributes = True


class CuentaMeResponse(BaseModel):
    id: UUID
    correo: str
    pais_iso: str
    rol: str
    estado: str
    fecha_alta: datetime
    suscripcion_activa: Optional[str] = None
    perfiles: List[PerfilResumen]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    cuenta: CuentaMeResponse