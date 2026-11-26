CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. CUENTA_SUSCRIPTOR
CREATE TABLE cuenta_suscriptor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correo VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    pais_iso CHAR(2) NOT NULL DEFAULT 'MX',
    rol VARCHAR(20) NOT NULL DEFAULT 'SUSCRIPTOR'
        CHECK (rol IN ('SUSCRIPTOR', 'ADMIN')),
    estado VARCHAR(30) NOT NULL DEFAULT 'ACTIVA'
        CHECK (estado IN ('PENDIENTE_VERIFICACION', 'ACTIVA', 'SUSPENDIDA', 'CERRADA')),
    fecha_alta TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. PERFIL
CREATE TABLE perfil (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cuenta_id UUID NOT NULL REFERENCES cuenta_suscriptor(id) ON DELETE CASCADE,
    nombre VARCHAR(50) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    clasificacion_maxima VARCHAR(10) NOT NULL DEFAULT 'MAS_18'
        CHECK (clasificacion_maxima IN ('TODOS', 'MAS_12', 'MAS_15', 'MAS_18')),
    hash_nip VARCHAR(128),
    intentos_nip_fallidos INT NOT NULL DEFAULT 0,
    nip_bloqueado_hasta TIMESTAMPTZ,
    es_titular BOOLEAN NOT NULL DEFAULT FALSE
);

-- 3. PLAN_PAGO
CREATE TABLE plan_pago (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(30) UNIQUE NOT NULL,
    precio NUMERIC(10, 2) NOT NULL,
    moneda CHAR(3) NOT NULL DEFAULT 'MXN',
    limite_pantallas INT NOT NULL CHECK (limite_pantallas > 0),
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 4. SUSCRIPCION
CREATE TABLE suscripcion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cuenta_id UUID NOT NULL REFERENCES cuenta_suscriptor(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES plan_pago(id),
    estado VARCHAR(30) NOT NULL
        CHECK (estado IN ('PENDIENTE_PAGO', 'ACTIVA', 'CANCELADA_CON_VIGENCIA', 'FINALIZADA')),
    inicio_ciclo TIMESTAMPTZ,
    fin_ciclo TIMESTAMPTZ,
    renovacion_automatica BOOLEAN NOT NULL DEFAULT TRUE,
    version INT NOT NULL DEFAULT 1
);

-- 5. COMPROBANTE_PAGO
CREATE TABLE comprobante_pago (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    suscripcion_id UUID NOT NULL REFERENCES suscripcion(id) ON DELETE CASCADE,
    monto NUMERIC(10, 2) NOT NULL,
    estado VARCHAR(20) NOT NULL
        CHECK (estado IN ('PENDIENTE', 'CONFIRMADO', 'RECHAZADO')),
    referencia_pasarela VARCHAR(100) UNIQUE,
    codigo_rechazo VARCHAR(50),
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. CONTENIDO
CREATE TABLE contenido (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo VARCHAR(200) NOT NULL,
    sinopsis TEXT,
    duracion_seg INT NOT NULL CHECK (duracion_seg > 0),
    clasificacion VARCHAR(10) NOT NULL
        CHECK (clasificacion IN ('TODOS', 'MAS_12', 'MAS_15', 'MAS_18')),
    url_stream VARCHAR(500) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 7. PUBLICACION (Licencias territoriales RN-03)
CREATE TABLE publicacion (
    contenido_id UUID NOT NULL REFERENCES contenido(id) ON DELETE CASCADE,
    codigo_pais CHAR(2) NOT NULL,
    visible_desde TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    visible_hasta TIMESTAMPTZ,
    PRIMARY KEY (contenido_id, codigo_pais)
);

-- 8. HISTORIAL_REPRODUCCION
CREATE TABLE historial_reproduccion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    perfil_id UUID NOT NULL REFERENCES perfil(id) ON DELETE CASCADE,
    contenido_id UUID NOT NULL REFERENCES contenido(id) ON DELETE CASCADE,
    dispositivo_id VARCHAR(64) NOT NULL,
    inicio TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fin TIMESTAMPTZ,
    posicion_final_seg INT NOT NULL DEFAULT 0,
    completado BOOLEAN NOT NULL DEFAULT FALSE
);

-- ==========================================
-- DATOS SEMILLA: PLANES Y CATÁLOGO INICIAL
-- ==========================================

INSERT INTO plan_pago (id, nombre, precio, moneda, limite_pantallas, activo) VALUES
    ('11111111-1111-1111-1111-111111111101', 'Básico', 139.00, 'MXN', 1, TRUE),
    ('11111111-1111-1111-1111-111111111102', 'Estándar', 219.00, 'MXN', 2, TRUE),
    ('11111111-1111-1111-1111-111111111103', 'Premium', 299.00, 'MXN', 4, TRUE);

INSERT INTO contenido (id, titulo, sinopsis, duracion_seg, clasificacion, url_stream, activo) VALUES
    (
        '22222222-2222-2222-2222-222222222201',
        'Big Buck Bunny',
        'Aventura animada para toda la familia en el bosque.',
        596,
        'TODOS',
        'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
        TRUE
    ),
    (
        '22222222-2222-2222-2222-222222222202',
        'Sintel: La Búsqueda del Dragón',
        'Una joven guerrera recorre tierras lejanas buscando a su dragón.',
        888,
        'MAS_12',
        'https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8',
        TRUE
    ),
    (
        '22222222-2222-2222-2222-222222222203',
        'Tears of Steel',
        'Ciencia ficción cyberpunk en Ámsterdam. Requiere validación de edad/NIP.',
        734,
        'MAS_18',
        'https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8',
        TRUE
    ),
    (
        '22222222-2222-2222-2222-222222222204',
        'Exclusiva Norteamérica: Elephants Dream',
        'Título licenciado únicamente en Estados Unidos (US) para pruebas RN-03.',
        653,
        'MAS_15',
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
        TRUE
    );

-- Publicaciones por país:
-- Títulos 1, 2 y 3 visibles en MX; Títulos 1 y 4 visibles en US
INSERT INTO publicacion (contenido_id, codigo_pais, visible_desde, visible_hasta) VALUES
    ('22222222-2222-2222-2222-222222222201', 'MX', NOW() - INTERVAL '1 day', NULL),
    ('22222222-2222-2222-2222-222222222202', 'MX', NOW() - INTERVAL '1 day', NULL),
    ('22222222-2222-2222-2222-222222222203', 'MX', NOW() - INTERVAL '1 day', NULL),
    ('22222222-2222-2222-2222-222222222201', 'US', NOW() - INTERVAL '1 day', NULL),
    ('22222222-2222-2222-2222-222222222204', 'US', NOW() - INTERVAL '1 day', NULL);