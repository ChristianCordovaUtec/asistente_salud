/*
import { useEffect, useRef, useState } from 'react'
import {
  useConversation,
  useConversationClientTool,
} from '@elevenlabs/react'

import {
  reconocerGlucosa,
  registrarLectura,
  type ResultadoOCR,
} from './services/ocr'

const AGENT_ID = 'agent_5001m67x3cdyf9a8pcxccpy2qavp'
const PACIENTE_ID = 'e4d7aaec-4c53-4a9c-8fba-69b687a6d248'

function App() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const guardandoRef = useRef(false)

  const [camaraActiva, setCamaraActiva] = useState(false)
  const [procesando, setProcesando] = useState(false)
  const [guardando, setGuardando] = useState(false)
  const [resultado, setResultado] = useState<ResultadoOCR | null>(null)
  const [valorConfirmado, setValorConfirmado] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')

  const {
    startSession,
    endSession,
    status,
    isSpeaking,
    isListening,
  } = useConversation()

  useEffect(() => {
    if (camaraActiva && streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current
    }
  }, [camaraActiva])

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach(track => track.stop())
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

      return 'Cámara activada. Indica al paciente que tome la fotografía.'
    } catch {
      setError('No se pudo acceder a la cámara.')
      return 'No se pudo activar la cámara. Informa al paciente.'
    }
  }

  const cerrarCamara = () => {
    streamRef.current?.getTracks().forEach(track => track.stop())
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

    const blob = await new Promise<Blob | null>(resolve =>
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
      } else {
        setError('No se pudo reconocer un valor de glucosa.')
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al procesar la imagen.')
    } finally {
      setProcesando(false)
    }
  }

  // Herramienta 1: activar la cámara desde Abu.
  useConversationClientTool('iniciar_captura_glucosa', async () => {
    return await iniciarCamara()
  })

  // Herramienta 2: entregar el resultado OCR a Abu.
  useConversationClientTool('obtener_resultado_ocr', () => {
    if (!resultado?.lectura_valida || resultado.glucosa === null) {
      return {
        lectura_valida: false,
        mensaje: 'Todavía no existe una lectura OCR válida.',
      }
    }

    return {
      lectura_valida: true,
      valor_ocr: resultado.glucosa,
      unidad: resultado.unidad || 'mg/dL',
      valor_actual: Number(valorConfirmado),
    }
  })

  // Herramienta 3: guardar después de la confirmación explícita.
  useConversationClientTool('confirmar_lectura_glucosa', async () => {
    if (guardandoRef.current) {
      return { exito: false, mensaje: 'El registro ya está en proceso.' }
    }

    if (!resultado?.lectura_valida || resultado.glucosa === null) {
      return { exito: false, mensaje: 'No existe una lectura válida pendiente.' }
    }

    const valor = Number(valorConfirmado)

    if (!Number.isFinite(valor) || valor <= 0) {
      return { exito: false, mensaje: 'El valor confirmado no es válido.' }
    }

    guardandoRef.current = true
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

      return {
        exito: true,
        valor_guardado: valor,
        mensaje: 'La lectura fue registrada correctamente en la base de datos.',
      }
    } catch (e) {
      const detalle = e instanceof Error ? e.message : 'Error al guardar.'
      setError(detalle)

      return { exito: false, mensaje: detalle }
    } finally {
      guardandoRef.current = false
      setGuardando(false)
    }
  })

  const iniciarConversacion = async () => {
    try {
        setError('')
        await startSession({
        agentId: AGENT_ID,
        })
    } catch (e) {
        console.error('Error iniciando Abu:', e)
        setError(e instanceof Error ? e.message : 'No se pudo conectar con Abu.')
    }
    }

  return (
    <main className="abu-container">
      <section className="abu-card">
        <div className="abu-avatar">A</div>

        <h1>¡Hola! Soy Abu</h1>
        <p className="abu-subtitle">Tu asistente personal de salud</p>

        <p className="abu-description">
          Estoy aquí para ayudarte a cuidar tu salud.
        </p>

        {status !== 'connected' ? (
          <button
            className="abu-button"
            onClick={iniciarConversacion}
            disabled={status === 'connecting'}
          >
            {status === 'connecting' ? 'Conectando...' : 'Conversar con Abu'}
          </button>
        ) : (
          <>
            <p>
              {isSpeaking ? 'Abu está hablando...' :
                isListening ? 'Abu te está escuchando...' : 'Conversación activa'}
            </p>

            <button className="abu-secondary-button" onClick={endSession}>
              Finalizar conversación
            </button>
          </>
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
            Leyendo el glucómetro...
          </p>
        )}

        {resultado?.lectura_valida && (
          <div className="camera-section">
            <h2>Revisa tu lectura</h2>
            <p>Abu detectó: {resultado.glucosa} {resultado.unidad}</p>

            <label htmlFor="valor-glucosa">Valor confirmado</label>
            <input
              id="valor-glucosa"
              type="number"
              min="0.01"
              step="any"
              value={valorConfirmado}
              onChange={e => setValorConfirmado(e.target.value)}
            />

            <p className="abu-description">
              Puedes corregir el valor aquí antes de confirmarlo por voz.
            </p>
          </div>
        )}

        {!camaraActiva && !resultado && !procesando && status === 'disconnected' && (
          <button className="abu-secondary-button" onClick={iniciarCamara}>
            Registrar glucosa sin voz
          </button>
        )}

        {guardando && <p>Guardando lectura...</p>}
        {mensaje && <p>{mensaje}</p>}
        {error && <p className="abu-error">{error}</p>}
      </section>
    </main>
  )
}

export default App
*/

import { useConversationControls, useConversationStatus } from '@elevenlabs/react'

function App() {
  const { startSession, endSession } = useConversationControls()
  const { status } = useConversationStatus()

  return (
    <div>
      <p>Estado: {status}</p>

      <button onClick={() => startSession({
        agentId: 'agent_5001m67x3cdyf9a8pcxccpy2qavp',
      })}>
        Conectar con Abu
      </button>

      <button onClick={() => endSession()}>
        Desconectar
      </button>
    </div>
  )
}

export default App
