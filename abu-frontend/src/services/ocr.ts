// TODO: Implementar manejo de errores más robusto y validaciones adicionales para la imagen.

const API_URL = 'http://127.0.0.1:5000'

export interface ResultadoOCR {
  lectura_valida: boolean
  glucosa: number | null
  unidad: string | null
  banderas: string[]
  leidos: unknown[]
}

export async function reconocerGlucosa(
  imagen: File
): Promise<ResultadoOCR> {
  const formData = new FormData()
  formData.append('imagen', imagen)

  const response = await fetch(`${API_URL}/api/ocr/glucometro`, {
    method: 'POST',
    body: formData,
  })

  const resultado = await response.json()

  if (!response.ok) {
    throw new Error(resultado.error || 'Error al procesar la imagen.')
  }

  return resultado as ResultadoOCR
}


export interface NuevaLectura {
  valor_ocr: number
  valor_confirmado: number
  unidad: string
  fecha_medicion: string
}

export async function registrarLectura(
  pacienteId: string,
  lectura: NuevaLectura
) {
  const response = await fetch(
    `${API_URL}/api/pacientes/${pacienteId}/lecturas-glucometro`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(lectura),
    }
  )

  const resultado = await response.json()

  if (!response.ok) {
    throw new Error(resultado.error || 'No se pudo guardar la lectura.')
  }

  return resultado
}
