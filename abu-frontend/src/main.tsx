import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConversationProvider } from '@elevenlabs/react'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConversationProvider
        onConnect={() => console.log('ABU CONECTADO')}
        onDisconnect={(details) => {
            console.log('CALLBACK DISCONNECT:', details)
            console.log('TIPO:', typeof details)
            console.log('JSON:', JSON.stringify(details))
            }}
        onError={(error) => {
            console.error('ERROR DEL AGENTE:', error)
        }}
        >
        <App />
    </ConversationProvider>
  </React.StrictMode>,
)