
import { useEffect, useRef, useState } from 'react'
import {
  reconocerGlucosa,
  registrarLectura,
  type ResultadoOCR,
} from './services/ocr'

// TODO: por ahora un solo paciente ya creado en BD
const PACIENTE_ID = 'e4d7aaec-4c53-4a9c-8fba-69b687a6d248'


function App() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const [camaraActiva, setCamaraActiva] = useState(false)
  const [procesando, setProcesando] = useState(false)
  const [guardando, setGuardando] = useState(false)
  const [resultado, setResultado] = useState<ResultadoOCR | null>(null)
  const [valorConfirmado, setValorConfirmado] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (camaraActiva && streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current
    }
  }, [camaraActiva])

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop())
    }
  }, [])

  const iniciarCamara = async () => {
    try {
      setError('')
      setMensaje('')
      setResultado(null)
      setValorConfirmado('')

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' } },
        audio: false,
      })

      streamRef.current = stream
      setCamaraActiva(true)
    } catch {
      setError('No se pudo acceder a la cámara. Verifica los permisos.')
    }
  }

  const cerrarCamara = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    setCamaraActiva(false)
  }

  const tomarFotografia = async () => {
    const video = videoRef.current
    if (!video || !video.videoWidth) return

    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const context = canvas.getContext('2d')
    if (!context) return

    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, 'image/jpeg', 0.9)
    )

    if (!blob) {
      setError('No se pudo capturar la fotografía.')
      return
    }

    const imagen = new File([blob], 'glucometro.jpg', {
      type: 'image/jpeg',
    })

    cerrarCamara()
    setProcesando(true)
    setError('')
    setMensaje('')

    try {
      const respuesta = await reconocerGlucosa(imagen)
      setResultado(respuesta)

      if (respuesta.lectura_valida && respuesta.glucosa !== null) {
        setValorConfirmado(String(respuesta.glucosa))
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al procesar la imagen.')
    } finally {
      setProcesando(false)
    }
  }

  const confirmarLectura = async () => {
    if (!resultado || resultado.glucosa === null) return

    const valor = Number(valorConfirmado)

    if (!Number.isFinite(valor) || valor <= 0) {
      setError('Ingresa un valor de glucosa válido.')
      return
    }

    setGuardando(true)
    setError('')

    try {
      await registrarLectura(PACIENTE_ID, {
        valor_ocr: resultado.glucosa,
        valor_confirmado: valor,
        unidad: resultado.unidad || 'mg/dL',
        fecha_medicion: new Date().toISOString(),
      })

      setMensaje('¡Lectura registrada correctamente!')
      setResultado(null)
      setValorConfirmado('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo guardar la lectura.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <main className="abu-container">
      <section className="abu-card">
        <div className="abu-avatar">A</div>

        <h1>¡Hola! Soy Abu</h1>

        <p className="abu-subtitle">
          Tu asistente personal de salud
        </p>

        <p className="abu-description">
          Estoy aquí para ayudarte a cuidar tu salud.
          Podemos registrar tus mediciones de glucosa
          de manera sencilla.
        </p>

        {!camaraActiva && !resultado && !procesando && !mensaje && (
          <button className="abu-button" onClick={iniciarCamara}>
            Registrar glucosa
          </button>
        )}

        {camaraActiva && (
          <div className="camera-section">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="camera-preview"
            />

            <button className="abu-button" onClick={tomarFotografia}>
              Tomar fotografía
            </button>

            <button className="abu-secondary-button" onClick={cerrarCamara}>
              Cancelar
            </button>
          </div>
        )}

        {procesando && (
          <p className="abu-description">
            Estoy leyendo tu glucómetro. Un momento, por favor...
          </p>
        )}

        {resultado && (
          <div className="camera-section">
            {resultado.lectura_valida ? (
              <>
                <h2>Revisa tu lectura</h2>

                <p>Abu detectó: {resultado.glucosa} {resultado.unidad}</p>

                <label htmlFor="valor-glucosa">
                  ¿Cuál es el valor correcto?
                </label>

                <input
                  id="valor-glucosa"
                  type="number"
                  min="0.01"
                  step="any"
                  value={valorConfirmado}
                  onChange={(e) => setValorConfirmado(e.target.value)}
                />

                <button
                  className="abu-button"
                  onClick={confirmarLectura}
                  disabled={guardando}
                >
                  {guardando ? 'Guardando...' : 'Confirmar lectura'}
                </button>
              </>
            ) : (
              <>
                <h2>No pude leer el glucómetro</h2>
                <p>Intenta tomar otra fotografía con mejor iluminación.</p>
              </>
            )}

            <button
              className="abu-secondary-button"
              onClick={iniciarCamara}
              disabled={guardando}
            >
              Tomar otra fotografía
            </button>
          </div>
        )}

        {mensaje && (
          <div>
            <p>{mensaje}</p>
            <button className="abu-button" onClick={iniciarCamara}>
              Registrar otra lectura
            </button>
          </div>
        )}

        {error && <p className="abu-error">{error}</p>}
      </section>
    </main>
  )
}

export default App
