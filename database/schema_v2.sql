-- =========================================================
-- ABU - schema_v2.sql
-- Version 2: lecturas de glucosa, alertas y notificaciones
-- Motor: PostgreSQL
--
-- Incluye:
--   1. responsable
--   2. paciente
--   3. paciente_responsable
--   4. perfil_corporal
--   5. tipo_condicion
--   6. condicion_paciente
--   7. lectura_glucometro
--   8. configuracion_alertas_glucosa
--   9. alerta
--  10. notificacion
-- =========================================================

-- Para generar UUID automáticamente
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================================================
-- 1. RESPONSABLE
-- Personas que pueden estar asociadas a uno o varios pacientes.
-- No se incluyen credenciales de acceso en esta version.
-- =========================================================

CREATE TABLE responsable (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    telefono VARCHAR(30) NOT NULL, -- requerido para contacto con el responsable
    email VARCHAR(150),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================
-- 2. PACIENTE
-- Personas cuyos datos de salud seran registrados.
-- En esta version, un paciente no puede ser responsable.
-- =========================================================

CREATE TABLE paciente (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,

    documento_pais CHAR(2) NOT NULL, -- ISO 3166-1 alpha-2: por ejemplo 'PE' para Perú
    tipo_documento VARCHAR(20) NOT NULL
        CHECK (
            tipo_documento IN ('DNI', 'CE', 'PASAPORTE', 'OTRO')
        ),
    documento_numero VARCHAR(30) NOT NULL,

    fecha_nacimiento DATE,
    sexo VARCHAR(20),
    telefono VARCHAR(30),

    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_paciente_documento
        UNIQUE (documento_pais, tipo_documento, documento_numero)
);

-- =========================================================
-- 3. PACIENTE_RESPONSABLE
-- Relacion muchos a muchos:
--   - Un paciente puede tener varios responsables.
--   - Un responsable puede estar asociado a varios pacientes.
-- La combinacion paciente-responsable no puede repetirse.
-- =========================================================

CREATE TABLE paciente_responsable (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    paciente_id UUID NOT NULL REFERENCES paciente(id),
    responsable_id UUID NOT NULL REFERENCES responsable(id),

    tipo_relacion VARCHAR(50) NOT NULL,
    tipo_relacion_otro VARCHAR(100),

    puede_ver BOOLEAN NOT NULL DEFAULT TRUE,
    puede_editar BOOLEAN NOT NULL DEFAULT FALSE,

    desde TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hasta TIMESTAMPTZ,

    CONSTRAINT uq_paciente_responsable
        UNIQUE (paciente_id, responsable_id),

    CONSTRAINT ck_paciente_responsable_fechas
        CHECK (hasta IS NULL OR hasta >= desde)
);

-- =========================================================
-- 4. PERFIL_CORPORAL
-- Historial de valores corporales del paciente.
-- Se permiten multiples registros por paciente. 
-- Esos valores suelen cambiar con el tiempo
-- =========================================================

CREATE TABLE perfil_corporal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    paciente_id UUID NOT NULL REFERENCES paciente(id),

    peso_kg NUMERIC(6,2),
    altura_cm NUMERIC(6,2),
    horas_sueno_promedio NUMERIC(4,2),

    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_perfil_peso
        CHECK (peso_kg IS NULL OR peso_kg > 0),

    CONSTRAINT ck_perfil_altura
        CHECK (altura_cm IS NULL OR altura_cm > 0),

    CONSTRAINT ck_perfil_sueno
        CHECK (
            horas_sueno_promedio IS NULL
            OR horas_sueno_promedio BETWEEN 0 AND 24
        )
);

-- =========================================================
-- 5. TIPO_CONDICION
-- Catalogo inicial de condiciones de salud.
-- =========================================================

CREATE TABLE tipo_condicion (
    id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, -- secuencial automatico
    nombre VARCHAR(80) NOT NULL UNIQUE
);

INSERT INTO tipo_condicion (nombre)
VALUES
    ('Diabetes'),
    ('Hipertensión');

-- =========================================================
-- 6. CONDICION_PACIENTE
-- Condiciones asociadas a cada paciente.
-- =========================================================

CREATE TABLE condicion_paciente (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    paciente_id UUID NOT NULL REFERENCES paciente(id),
    tipo_condicion_id SMALLINT NOT NULL REFERENCES tipo_condicion(id),

    estado VARCHAR(20) NOT NULL
        CHECK (
            estado IN (
                'activa', -- condición presente y requiere seguimiento.
                'controlada', -- condición presente, pero se encuentra bajo control.
                'en_remision', -- disminución o ausencia temporal de manifestaciones.
                'inactiva' -- condición ya no se considera vigente o cerrada en el registro clínico.
            )
        ),

    fuente TEXT, -- de dónde proviene la información sobre la condición del paciente
    fecha_diagnosticada DATE,
    fecha_actualizada TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_paciente_tipo_condicion
        UNIQUE (paciente_id, tipo_condicion_id)
);

-- =========================================================
-- 7. LECTURA_GLUCOMETRO
-- Lecturas de glucosa obtenidas mediante OCR y confirmadas
-- por el paciente antes de ser almacenadas.
-- =========================================================

CREATE TABLE lectura_glucometro (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id UUID NOT NULL REFERENCES paciente(id),

    valor_ocr NUMERIC(6,2) NOT NULL,
    valor_confirmado NUMERIC(6,2) NOT NULL,
    unidad VARCHAR(10) NOT NULL DEFAULT 'mg/dL'
        CHECK (unidad IN ('mg/dL', 'mmol/L')),

    fecha_medicion TIMESTAMPTZ NOT NULL,
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_lectura_glucometro_valor_ocr
        CHECK (valor_ocr > 0),
    CONSTRAINT ck_lectura_glucometro_valor_confirmado
        CHECK (valor_confirmado > 0)
);

-- =========================================================
-- 8. CONFIGURACION_ALERTAS_GLUCOSA
-- Configuracion de umbrales y deteccion de tendencias
-- para cada paciente. Cada paciente tiene una configuracion.
-- =========================================================

CREATE TABLE configuracion_alertas_glucosa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id UUID NOT NULL REFERENCES paciente(id),

    umbral_minimo NUMERIC(6,2),
    umbral_maximo NUMERIC(6,2),
    unidad VARCHAR(10) NOT NULL DEFAULT 'mg/dL'
        CHECK (unidad IN ('mg/dL', 'mmol/L')),

    detectar_tendencia BOOLEAN NOT NULL DEFAULT FALSE,
    dias_analisis SMALLINT NOT NULL DEFAULT 4,

    activa BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_configuracion_alertas_paciente
        UNIQUE (paciente_id),

    CONSTRAINT ck_configuracion_alertas_umbrales
        CHECK (
            (umbral_minimo IS NULL OR umbral_minimo > 0)
            AND (umbral_maximo IS NULL OR umbral_maximo > 0)
            AND (
                umbral_minimo IS NULL
                OR umbral_maximo IS NULL
                OR umbral_minimo < umbral_maximo
            )
        ),

    CONSTRAINT ck_configuracion_alertas_dias
        CHECK (
            (detectar_tendencia = FALSE AND dias_analisis = 4)
            OR (detectar_tendencia = TRUE AND dias_analisis >= 1)
        )
);

-- =========================================================
-- 9. ALERTA
-- Eventos generados cuando una lectura o una tendencia
-- cumple alguna de las condiciones configuradas.
-- Una alerta por tendencia puede estar asociada a varias
-- lecturas, por eso lectura_id permite NULL.
-- =========================================================

CREATE TABLE alerta (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id UUID NOT NULL REFERENCES paciente(id),
    lectura_id UUID REFERENCES lectura_glucometro(id),

    tipo VARCHAR(30) NOT NULL
        CHECK (tipo IN ('umbral_glucosa', 'tendencia_glucosa')),

    descripcion TEXT NOT NULL,
    valor_detectado NUMERIC(6,2),

    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'atendida', 'cerrada')),

    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_alerta_valor_detectado
        CHECK (valor_detectado IS NULL OR valor_detectado > 0)
);

-- =========================================================
-- 10. NOTIFICACION
-- Mensajes enviados a los responsables para informarles
-- sobre las alertas generadas para sus pacientes.
-- Se conserva el destinatario utilizado en cada envio.
-- =========================================================

CREATE TABLE notificacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alerta_id UUID NOT NULL REFERENCES alerta(id),
    paciente_responsable_id UUID NOT NULL REFERENCES paciente_responsable(id),

    canal VARCHAR(20) NOT NULL
        CHECK (canal IN ('whatsapp', 'email', 'web')),

    destinatario VARCHAR(150) NOT NULL,
    mensaje TEXT NOT NULL,

    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'enviada', 'entregada', 'fallida')),

    proveedor VARCHAR(50),
    proveedor_mensaje_id VARCHAR(150),

    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_envio TIMESTAMPTZ,
    fecha_entrega TIMESTAMPTZ,

    error_detalle TEXT
);

-- =========================================================
-- INDICES
-- =========================================================

CREATE INDEX idx_paciente_responsable_responsable
    ON paciente_responsable(responsable_id);

CREATE INDEX idx_perfil_corporal_paciente_fecha
    ON perfil_corporal(paciente_id, fecha_registro DESC);

CREATE INDEX idx_condicion_paciente_paciente
    ON condicion_paciente(paciente_id);

CREATE INDEX idx_lectura_glucometro_paciente_fecha
    ON lectura_glucometro(paciente_id, fecha_medicion DESC);

CREATE INDEX idx_alerta_paciente_fecha
    ON alerta(paciente_id, fecha_registro DESC);

CREATE INDEX idx_notificacion_alerta
    ON notificacion(alerta_id);

CREATE INDEX idx_notificacion_paciente_responsable
    ON notificacion(paciente_responsable_id);

-- =========================================================
-- FIN VERSION 2
-- =========================================================
