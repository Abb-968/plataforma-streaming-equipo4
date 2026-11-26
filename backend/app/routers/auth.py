from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CuentaSuscriptor, Perfil, Suscripcion
from app.schemas import (
    CuentaMeResponse,
    LoginRequest,
    PerfilResumen,
    RegistroRequest,
    TokenResponse,
)
from app.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["SS-01 Identidad y Autenticación"])


def _armar_respuesta_cuenta(
    cuenta: CuentaSuscriptor, db: Session
) -> CuentaMeResponse:
    suscripcion = (
        db.query(Suscripcion)
        .filter(
            Suscripcion.cuenta_id == cuenta.id,
            Suscripcion.estado.in_(["ACTIVA", "CANCELADA_CON_VIGENCIA"]),
        )
        .first()
    )
    perfiles_resumen = [
        PerfilResumen(
            id=p.id,
            nombre=p.nombre,
            clasificacion_maxima=p.clasificacion_maxima,
            es_titular=p.es_titular,
            tiene_nip=bool(p.hash_nip),
        )
        for p in cuenta.perfiles
    ]
    return CuentaMeResponse(
        id=cuenta.id,
        correo=cuenta.correo,
        pais_iso=cuenta.pais_iso,
        rol=cuenta.rol,
        estado=cuenta.estado,
        fecha_alta=cuenta.fecha_alta,
        suscripcion_activa=suscripcion.plan.nombre if suscripcion else None,
        perfiles=perfiles_resumen,
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nueva cuenta de suscriptor y perfil titular",
)
def registrar_suscriptor(datos: RegistroRequest, db: Session = Depends(get_db)):
    correo_normalizado = datos.correo.strip().lower()
    existente = (
        db.query(CuentaSuscriptor)
        .filter(CuentaSuscriptor.correo == correo_normalizado)
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya se encuentra registrado",
        )

    nueva_cuenta = CuentaSuscriptor(
        correo=correo_normalizado,
        password_hash=get_password_hash(datos.password),
        pais_iso=datos.pais_iso.upper(),
        rol="SUSCRIPTOR",
        estado="ACTIVA",
    )
    db.add(nueva_cuenta)
    db.flush()

    perfil_titular = Perfil(
        cuenta_id=nueva_cuenta.id,
        nombre=datos.nombre_perfil_titular.strip(),
        fecha_nacimiento=datos.fecha_nacimiento,
        clasificacion_maxima="MAS_18",
        es_titular=True,
    )
    db.add(perfil_titular)
    db.commit()
    db.refresh(nueva_cuenta)

    token = create_access_token(nueva_cuenta)
    return TokenResponse(
        access_token=token,
        cuenta=_armar_respuesta_cuenta(nueva_cuenta, db),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión y obtener token JWT",
)
def iniciar_sesion(datos: LoginRequest, db: Session = Depends(get_db)):
    correo_normalizado = datos.correo.strip().lower()
    cuenta = (
        db.query(CuentaSuscriptor)
        .filter(CuentaSuscriptor.correo == correo_normalizado)
        .first()
    )
    if not cuenta or not verify_password(datos.password, cuenta.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    if cuenta.estado != "ACTIVA":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"La cuenta se encuentra en estado {cuenta.estado}",
        )

    token = create_access_token(cuenta)
    return TokenResponse(
        access_token=token,
        cuenta=_armar_respuesta_cuenta(cuenta, db),
    )


@router.get(
    "/me",
    response_model=CuentaMeResponse,
    summary="Consultar datos de la cuenta autenticada y sus perfiles",
)
def obtener_cuenta_actual(
    cuenta: CuentaSuscriptor = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _armar_respuesta_cuenta(cuenta, db)