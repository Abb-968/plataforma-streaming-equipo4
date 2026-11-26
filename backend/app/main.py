from datetime import date, datetime, timedelta, timezone
from uuid import UUID
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import SessionLocal
from app.models import (
    ComprobantePago,
    CuentaSuscriptor,
    Perfil,
    PlanPago,
    Suscripcion,
)
from app.routers import auth
from app.security import get_password_hash

app = FastAPI(
    title="API Plataforma de Streaming - Equipo 4",
    description="MVP SCRUM trazado a los subsistemas SS-01 a SS-08 del diseño RUP.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def cargar_cuentas_demo():
    db = SessionLocal()
    try:
        if db.query(CuentaSuscriptor).first():
            return

        ahora = datetime.now(timezone.utc)
        pw_demo = get_password_hash("Demo1234!")
        nip_demo = get_password_hash("1234")

        # 1. Suscriptor México con Plan Estándar activo + Perfil adulto y Perfil infantil con NIP 1234
        cuenta_mx = CuentaSuscriptor(
            id=UUID("33333333-3333-3333-3333-333333333301"),
            correo="suscriptor@equipo4.mx",
            password_hash=pw_demo,
            pais_iso="MX",
            rol="SUSCRIPTOR",
            estado="ACTIVA",
        )
        db.add(cuenta_mx)
        db.flush()

        db.add_all(
            [
                Perfil(
                    cuenta_id=cuenta_mx.id,
                    nombre="Abigail (Titular)",
                    fecha_nacimiento=date(2004, 5, 9),
                    clasificacion_maxima="MAS_18",
                    hash_nip=nip_demo,
                    es_titular=True,
                ),
                Perfil(
                    cuenta_id=cuenta_mx.id,
                    nombre="Infantil",
                    fecha_nacimiento=date(2017, 3, 15),
                    clasificacion_maxima="TODOS",
                    hash_nip=nip_demo,
                    es_titular=False,
                ),
            ]
        )

        plan_estandar = (
            db.query(PlanPago)
            .filter(PlanPago.nombre == "Estándar")
            .first()
        )
        if plan_estandar:
            sus_mx = Suscripcion(
                cuenta_id=cuenta_mx.id,
                plan_id=plan_estandar.id,
                estado="ACTIVA",
                inicio_ciclo=ahora,
                fin_ciclo=ahora + timedelta(days=30),
                renovacion_automatica=True,
            )
            db.add(sus_mx)
            db.flush()
            db.add(
                ComprobantePago(
                    suscripcion_id=sus_mx.id,
                    monto=plan_estandar.precio,
                    estado="CONFIRMADO",
                    referencia_pasarela="SEED-MX-0001",
                )
            )

        # 2. Suscriptor Estados Unidos con Plan Básico activo (para probar RN-03 territorial)
        cuenta_us = CuentaSuscriptor(
            id=UUID("33333333-3333-3333-3333-333333333302"),
            correo="usuario.us@equipo4.com",
            password_hash=pw_demo,
            pais_iso="US",
            rol="SUSCRIPTOR",
            estado="ACTIVA",
        )
        db.add(cuenta_us)
        db.flush()
        db.add(
            Perfil(
                cuenta_id=cuenta_us.id,
                nombre="John US",
                fecha_nacimiento=date(1998, 8, 20),
                clasificacion_maxima="MAS_18",
                es_titular=True,
            )
        )
        plan_basico = (
            db.query(PlanPago).filter(PlanPago.nombre == "Básico").first()
        )
        if plan_basico:
            sus_us = Suscripcion(
                cuenta_id=cuenta_us.id,
                plan_id=plan_basico.id,
                estado="ACTIVA",
                inicio_ciclo=ahora,
                fin_ciclo=ahora + timedelta(days=30),
                renovacion_automatica=True,
            )
            db.add(sus_us)

        # 3. Administrador del catálogo (SS-06 / SS-07)
        cuenta_admin = CuentaSuscriptor(
            id=UUID("33333333-3333-3333-3333-333333333303"),
            correo="admin@equipo4.mx",
            password_hash=pw_demo,
            pais_iso="MX",
            rol="ADMIN",
            estado="ACTIVA",
        )
        db.add(cuenta_admin)
        db.flush()
        db.add(
            Perfil(
                cuenta_id=cuenta_admin.id,
                nombre="Admin Equipo 4",
                fecha_nacimiento=date(2000, 1, 1),
                clasificacion_maxima="MAS_18",
                es_titular=True,
            )
        )

        db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    cargar_cuentas_demo()


app.include_router(auth.router)


@app.get("/", tags=["Salud"])
def root():
    return {"mensaje": "API Plataforma de Streaming - Equipo 4 activa"}


@app.get("/health", tags=["Salud"])
def health_check():
    return {"status": "ok", "servicio": "streaming_api"}