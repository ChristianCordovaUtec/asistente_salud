
import re

import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR


# Motor OCR: se inicializa una sola vez al cargar el módulo.
ENGINE = RapidOCR()

ROTACIONES = [
    None,
    cv2.ROTATE_90_CLOCKWISE,
    cv2.ROTATE_180,
    cv2.ROTATE_90_COUNTERCLOCKWISE,
]

ANCLAS = {
    "SYS": ("SYS", "SXS"),
    "DIA": ("DIA", "PIA"),
    "PUL": ("PUL",),
}


# ---------------------------------------------------------------------
# 1. Carga de imagen
# ---------------------------------------------------------------------

def cargar(imagen_bytes, lado_max=1600):
    """
    Decodifica una imagen recibida en memoria y ajusta su tamaño máximo.
    No guarda archivos en disco.
    """
    if not imagen_bytes:
        raise ValueError("La imagen está vacía.")

    buffer = np.frombuffer(imagen_bytes, dtype=np.uint8)
    img = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("No se pudo interpretar la imagen.")

    escala = lado_max / max(img.shape[:2])

    return cv2.resize(
        img,
        None,
        fx=escala,
        fy=escala,
        interpolation=cv2.INTER_AREA
    )


# ---------------------------------------------------------------------
# 2. OCR y detección de etiquetas
# ---------------------------------------------------------------------

def ocr(img, cls=True):
    """Ejecuta RapidOCR y devuelve los textos con sus coordenadas."""
    resultado, _ = ENGINE(img, use_cls=cls)

    tokens = []

    for caja, texto, confianza in resultado or []:
        caja = np.array(caja, dtype=float)

        tokens.append({
            "texto": texto,
            "conf": float(confianza),
            "cx": caja[:, 0].mean(),
            "cy": caja[:, 1].mean(),
            "h": np.ptp(caja[:, 1])
        })

    return tokens


def buscar_anclas(tokens):
    """Identifica las etiquetas SYS, DIA y PUL."""
    anclas = {}

    for token in tokens:
        texto = token["texto"].upper()

        for clave, variantes in ANCLAS.items():
            if clave not in anclas and any(
                variante in texto for variante in variantes
            ):
                anclas[clave] = token["cy"]

    # Inferir una etiqueta faltante cuando existen otras dos.
    if len(anclas) == 2:
        orden = ["SYS", "DIA", "PUL"]
        indices = sorted(orden.index(k) for k in anclas)

        posiciones = [anclas[orden[i]] for i in indices]

        paso = (
            (posiciones[1] - posiciones[0])
            / (indices[1] - indices[0])
        )

        faltante = [
            k for k in orden if k not in anclas
        ][0]

        anclas[faltante] = (
            posiciones[0]
            + (orden.index(faltante) - indices[0]) * paso
        )

    return anclas


# ---------------------------------------------------------------------
# 3. Orientación de imagen
# ---------------------------------------------------------------------

def orientar(img):
    """Prueba las cuatro orientaciones y selecciona la más legible."""
    mejor = None

    for rotacion in ROTACIONES:
        imagen = (
            img if rotacion is None
            else cv2.rotate(img, rotacion)
        )

        tokens = ocr(imagen)
        anclas = buscar_anclas(tokens)

        texto_ok = sum(
            token["conf"]
            for token in tokens
            if len(re.sub(
                r"[^A-Za-z]", "", token["texto"]
            )) >= 3
        )

        puntaje = 3 * len(anclas) + texto_ok

        if mejor is None or puntaje > mejor[0]:
            mejor = (puntaje, imagen, anclas)

    return mejor[1], mejor[2]


# ---------------------------------------------------------------------
# 4. Recorte de pantalla LCD
# ---------------------------------------------------------------------

def recortar_lcd(imagen, anclas):
    """Busca el contorno rectangular correspondiente a la pantalla."""
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

    alto, ancho = gris.shape

    bordes = cv2.dilate(
        cv2.Canny(
            cv2.GaussianBlur(gris, (5, 5), 0),
            30,
            90
        ),
        None,
        iterations=2
    )

    contornos, _ = cv2.findContours(
        bordes,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidatos = []

    for contorno in contornos:
        x, y, w, h = cv2.boundingRect(contorno)

        if (
            0.02 * alto * ancho < w * h < 0.5 * alto * ancho
            and 0.5 < w / h < 2.2
            and cv2.contourArea(contorno) > 0.6 * w * h
        ):
            candidatos.append((x, y, w, h))

    if not candidatos:
        return imagen

    if anclas:
        promedio_y = np.mean(list(anclas.values()))

        candidatos.sort(
            key=lambda b: (
                abs(b[1] + b[3] / 2 - promedio_y)
                - 0.0005 * b[2] * b[3]
            )
        )
    else:
        candidatos.sort(
            key=lambda b: -b[2] * b[3]
        )

    x, y, w, h = candidatos[0]

    return imagen[y:y + h, x:x + w]


# ---------------------------------------------------------------------
# 5. Variantes de imagen para OCR
# ---------------------------------------------------------------------

def variantes(lcd):
    """Genera imágenes procesadas para mejorar la lectura de dígitos."""
    gris_original = cv2.cvtColor(
        lcd,
        cv2.COLOR_BGR2GRAY
    )

    for lado in (700, 1100, 1500):
        escala = lado / max(gris_original.shape)

        gris = cv2.resize(
            gris_original,
            None,
            fx=escala,
            fy=escala,
            interpolation=cv2.INTER_CUBIC
        )

        gris = cv2.createCLAHE(
            2.5,
            (8, 8)
        ).apply(gris)

        kernel_size = int(max(3, gris.shape[0] / 90)) | 1

        unido = cv2.erode(
            gris,
            cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (kernel_size, kernel_size)
            )
        )

        for variante in (gris, unido):
            imagen = cv2.copyMakeBorder(
                variante,
                40, 40, 40, 40,
                cv2.BORDER_REPLICATE
            )

            yield imagen, escala, 40


# ---------------------------------------------------------------------
# 6. Lectura y agrupación de números
# ---------------------------------------------------------------------

def leer_numeros(lcd):
    """
    Lee números en distintas variantes de la pantalla LCD.
    Agrupa detecciones repetidas y selecciona la lectura más confiable.
    """
    candidatos = []

    for imagen, escala, padding in variantes(lcd):
        tokens = ocr(imagen, cls=False)

        for token in tokens:
            token["cx"] = (token["cx"] - padding) / escala
            token["cy"] = (token["cy"] - padding) / escala
            token["h"] = token["h"] / escala

            texto = token["texto"]

            # Ignorar fechas y horas.
            if re.search(r"[/:]", texto):
                continue

            limpio = re.sub(r"[^\d.]", "", texto)

            if not re.fullmatch(r"\d{1,3}(\.\d)?", limpio):
                continue

            token["valor"] = limpio
            candidatos.append(token)

    # Agrupar detecciones que corresponden al mismo número.
    grupos = []

    for token in sorted(
        candidatos,
        key=lambda t: -t["h"]
    ):
        for grupo in grupos:
            referencia = grupo[0]

            if (
                abs(referencia["cy"] - token["cy"])
                < 0.5 * referencia["h"]
                and abs(referencia["cx"] - token["cx"])
                < referencia["h"]
            ):
                grupo.append(token)
                break
        else:
            grupos.append([token])

    numeros = []

    for grupo in grupos:
        puntajes = {}

        for token in grupo:
            valor = token["valor"]
            puntajes[valor] = (
                puntajes.get(valor, 0) + token["conf"]
            )

        # En empate gana el valor con más dígitos.
        valor_elegido = max(
            puntajes,
            key=lambda v: (
                round(puntajes[v], 1),
                len(v)
            )
        )

        numeros.append({
            "valor": valor_elegido,
            "cy": np.mean([t["cy"] for t in grupo]),
            "h": max(t["h"] for t in grupo),
            "votos": len(grupo)
        })

    return numeros


# ---------------------------------------------------------------------
# 7. Asignación de valor de glucosa
# ---------------------------------------------------------------------

def asignar_glucometro(numeros):
    """
    Selecciona provisionalmente el número de mayor tamaño.

    TODO: mejorar la identificación del valor de glucosa considerando
    posición, características del equipo y posibles números adicionales.
    """
    if not numeros:
        return {
            "lectura_valida": False,
            "glucosa": None,
            "unidad": None,
            "banderas": ["sin_lectura"]
        }

    # TODO: validar esta heurística con fotografías reales.
    numero = max(
        numeros,
        key=lambda n: n["h"]
    )

    return {
        "lectura_valida": True,
        "glucosa": int(numero["valor"]),
        "unidad": "mg/dL",
        "banderas": []
    }


# ---------------------------------------------------------------------
# 8. Procesamiento principal
# ---------------------------------------------------------------------

def procesar_glucometro(imagen_bytes):
    """
    Procesa una imagen de glucómetro recibida en memoria.

    Retorna el valor OCR detectado y su estado de validez.
    No guarda la imagen ni registra datos en la base de datos.
    """
    imagen = cargar(imagen_bytes)

    imagen_orientada, anclas = orientar(imagen)

    lcd = recortar_lcd(
        imagen_orientada,
        anclas
    )

    numeros = leer_numeros(lcd)

    resultado = asignar_glucometro(numeros)

    resultado["leidos"] = [
        numero["valor"] for numero in numeros
    ]

    return resultado
