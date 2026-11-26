import os
from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CuentaSuscriptor

JWT_SECRET = os.getenv("JWT_SECRET", "equipo4_super_secreto_mvp_2026")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def get_password_hash(plain_text: str) -> str:
    return pwd_context.hash(plain_text)


def verify_password(plain_text: str, hashed_text: str) -> bool:
    return pwd_context.verify(plain_text, hashed_text)


def create_access_token(cuenta: CuentaSuscriptor) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(cuenta.id),
        "correo": cuenta.correo,
        "pais_iso": cuenta.pais_iso,
        "rol": cuenta.rol,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CuentaSuscriptor:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        cuenta_id = UUID(payload.get("sub"))
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT inválido o expirado",
        )

    cuenta = (
        db.query(CuentaSuscriptor)
        .filter(CuentaSuscriptor.id == cuenta_id)
        .first()
    )
    if not cuenta or cuenta.estado != "ACTIVA":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta inexistente o inactiva",
        )
    return cuenta