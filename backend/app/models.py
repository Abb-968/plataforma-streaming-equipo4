import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class CuentaSuscriptor(Base):
    __tablename__ = "cuenta_suscriptor"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    correo = Column(String(254), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    pais_iso = Column(String(2), nullable=False, default="MX")
    rol = Column(String(20), nullable=False, default="SUSCRIPTOR")
    estado = Column(String(30), nullable=False, default="ACTIVA")
    fecha_alta = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    perfiles = relationship(
        "Perfil", back_populates="cuenta", cascade="all, delete-orphan"
    )
    suscripciones = relationship(
        "Suscripcion", back_populates="cuenta", cascade="all, delete-orphan"
    )


class Perfil(Base):
    __tablename__ = "perfil"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cuenta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cuenta_suscriptor.id", ondelete="CASCADE"),
        nullable=False,
    )
    nombre = Column(String(50), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    clasificacion_maxima = Column(String(10), nullable=False, default="MAS_18")
    hash_nip = Column(String(128), nullable=True)
    intentos_nip_fallidos = Column(Integer, nullable=False, default=0)
    nip_bloqueado_hasta = Column(DateTime(timezone=True), nullable=True)
    es_titular = Column(Boolean, nullable=False, default=False)

    cuenta = relationship("CuentaSuscriptor", back_populates="perfiles")


class PlanPago(Base):
    __tablename__ = "plan_pago"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(30), unique=True, nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    moneda = Column(String(3), nullable=False, default="MXN")
    limite_pantallas = Column(Integer, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)


class Suscripcion(Base):
    __tablename__ = "suscripcion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cuenta_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cuenta_suscriptor.id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plan_pago.id"), nullable=False)
    estado = Column(String(30), nullable=False)
    inicio_ciclo = Column(DateTime(timezone=True), nullable=True)
    fin_ciclo = Column(DateTime(timezone=True), nullable=True)
    renovacion_automatica = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)

    cuenta = relationship("CuentaSuscriptor", back_populates="suscripciones")
    plan = relationship("PlanPago")


class ComprobantePago(Base):
    __tablename__ = "comprobante_pago"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    suscripcion_id = Column(
        UUID(as_uuid=True),
        ForeignKey("suscripcion.id", ondelete="CASCADE"),
        nullable=False,
    )
    monto = Column(Numeric(10, 2), nullable=False)
    estado = Column(String(20), nullable=False)
    referencia_pasarela = Column(String(100), unique=True, nullable=True)
    codigo_rechazo = Column(String(50), nullable=True)
    fecha = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class Contenido(Base):
    __tablename__ = "contenido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo = Column(String(200), nullable=False)
    sinopsis = Column(Text, nullable=True)
    duracion_seg = Column(Integer, nullable=False)
    clasificacion = Column(String(10), nullable=False)
    url_stream = Column(String(500), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)


class Publicacion(Base):
    __tablename__ = "publicacion"

    contenido_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contenido.id", ondelete="CASCADE"),
        primary_key=True,
    )
    codigo_pais = Column(String(2), primary_key=True)
    visible_desde = Column(DateTime(timezone=True), nullable=False)
    visible_hasta = Column(DateTime(timezone=True), nullable=True)


class HistorialReproduccion(Base):
    __tablename__ = "historial_reproduccion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    perfil_id = Column(
        UUID(as_uuid=True),
        ForeignKey("perfil.id", ondelete="CASCADE"),
        nullable=False,
    )
    contenido_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contenido.id", ondelete="CASCADE"),
        nullable=False,
    )
    dispositivo_id = Column(String(64), nullable=False)
    inicio = Column(DateTime(timezone=True), nullable=False)
    fin = Column(DateTime(timezone=True), nullable=True)
    posicion_final_seg = Column(Integer, nullable=False, default=0)
    completado = Column(Boolean, nullable=False, default=False)