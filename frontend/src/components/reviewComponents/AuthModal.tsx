import { useState } from 'react'
import { loginApi, registerApi } from '../../api/reviewApi'
import type { UserSession } from '../../types/reviewHome'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (user: UserSession) => void
}

export function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
  const [isRegister, setIsRegister] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [nombre, setNombre] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (!isOpen) return null

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const user = await loginApi(username, password)
      onSuccess(user)
      onClose()
    } catch (err: any) {
      setError(err.message || 'Credenciales incorrectas')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const user = await registerApi(username, password, nombre)
      onSuccess(user)
      onClose()
    } catch (err: any) {
      setError(err.message || 'Error al registrar la cuenta')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(20, 26, 23, 0.65)',
        backdropFilter: 'blur(5px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
        padding: '16px',
      }}
      onClick={onClose}
    >
      {/* Contenedor Principal con Sombra Elevada */}
      <div
        style={{
          position: 'relative',
          width: '740px',
          height: '460px',
          background: '#ffffff',
          borderRadius: '16px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.35)',
          overflow: 'hidden',
          display: 'flex',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Botón X de cerrar */}
        <button
          type="button"
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            zIndex: 40,
            background: 'none',
            border: 'none',
            fontSize: '22px',
            lineHeight: 1,
            color: '#67736b',
            cursor: 'pointer',
          }}
        >
          &times;
        </button>

        {/* ================= FORMULARIO LOGIN (Izquierda) ================= */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '50%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            padding: '40px',
            boxSizing: 'border-box',
            transition: 'all 0.6s ease-in-out',
            opacity: isRegister ? 0 : 1,
            pointerEvents: isRegister ? 'none' : 'auto',
            transform: isRegister ? 'translateX(-30px)' : 'translateX(0)',
            zIndex: 10,
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: '28px' }}>
            <h2 style={{ fontSize: '26px', fontWeight: 700, margin: '0 0 6px', color: '#1c2420' }}>
              Iniciar Sesión
            </h2>
            <div style={{ width: '38px', height: '3px', background: '#1c5547', margin: '0 auto', borderRadius: '2px' }} />
          </div>

          {error && !isRegister && (
            <div style={{ padding: '8px 12px', background: '#fdf0ef', color: '#9e362d', borderRadius: '6px', fontSize: '12px', marginBottom: '14px', textAlign: 'center' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Input Usuario con línea inferior */}
            <div style={{ position: 'relative', borderBottom: '1.5px solid #d1d9d4' }}>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Nombre de usuario"
                style={{
                  width: '100%',
                  border: 'none',
                  outline: 'none',
                  padding: '8px 28px 8px 4px',
                  fontSize: '14px',
                  color: '#252d29',
                  background: 'transparent',
                }}
              />
              <svg style={{ position: 'absolute', right: '4px', top: '9px', width: '16px', height: '16px', fill: '#67736b' }} viewBox="0 0 24 24">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
              </svg>
            </div>

            {/* Input Contraseña */}
            <div style={{ position: 'relative', borderBottom: '1.5px solid #d1d9d4' }}>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Contraseña"
                style={{
                  width: '100%',
                  border: 'none',
                  outline: 'none',
                  padding: '8px 28px 8px 4px',
                  fontSize: '14px',
                  color: '#252d29',
                  background: 'transparent',
                }}
              />
              <svg style={{ position: 'absolute', right: '4px', top: '9px', width: '16px', height: '16px', fill: '#67736b' }} viewBox="0 0 24 24">
                <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
              </svg>
            </div>

            {/* Botón Píldora */}
            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: '10px',
                padding: '12px',
                borderRadius: '24px',
                background: '#1c5547',
                color: '#ffffff',
                fontWeight: 600,
                fontSize: '14px',
                border: 'none',
                cursor: loading ? 'not-allowed' : 'pointer',
                boxShadow: '0 4px 12px rgba(28, 85, 71, 0.3)',
                transition: 'all 0.2s',
              }}
            >
              {loading ? 'Validando...' : 'Acceder'}
            </button>

            <p style={{ textAlign: 'center', fontSize: '12px', color: '#67736b', margin: '4px 0 0' }}>
              ¿No tienes una cuenta?{' '}
              <button
                type="button"
                onClick={() => { setIsRegister(true); setError(null); }}
                style={{ background: 'none', border: 'none', color: '#1c5547', fontWeight: 700, cursor: 'pointer', padding: 0 }}
              >
                Regístrate aquí
              </button>
            </p>
          </form>
        </div>

        {/* ================= FORMULARIO REGISTRO (Derecha) ================= */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '50%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            padding: '40px',
            boxSizing: 'border-box',
            transition: 'all 0.6s ease-in-out',
            opacity: isRegister ? 1 : 0,
            pointerEvents: isRegister ? 'auto' : 'none',
            transform: isRegister ? 'translateX(0)' : 'translateX(30px)',
            zIndex: 10,
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: '22px' }}>
            <h2 style={{ fontSize: '26px', fontWeight: 700, margin: '0 0 6px', color: '#1c2420' }}>
              Crear Cuenta
            </h2>
            <div style={{ width: '38px', height: '3px', background: '#1c5547', margin: '0 auto', borderRadius: '2px' }} />
          </div>

          {error && isRegister && (
            <div style={{ padding: '8px 12px', background: '#fdf0ef', color: '#9e362d', borderRadius: '6px', fontSize: '12px', marginBottom: '12px', textAlign: 'center' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Input Nombre */}
            <div style={{ position: 'relative', borderBottom: '1.5px solid #d1d9d4' }}>
              <input
                type="text"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Nombre completo"
                style={{
                  width: '100%',
                  border: 'none',
                  outline: 'none',
                  padding: '7px 28px 7px 4px',
                  fontSize: '13px',
                  color: '#252d29',
                  background: 'transparent',
                }}
              />
              <svg style={{ position: 'absolute', right: '4px', top: '8px', width: '15px', height: '15px', fill: '#67736b' }} viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
              </svg>
            </div>

            {/* Input Usuario */}
            <div style={{ position: 'relative', borderBottom: '1.5px solid #d1d9d4' }}>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Nombre de usuario"
                style={{
                  width: '100%',
                  border: 'none',
                  outline: 'none',
                  padding: '7px 28px 7px 4px',
                  fontSize: '13px',
                  color: '#252d29',
                  background: 'transparent',
                }}
              />
              <svg style={{ position: 'absolute', right: '4px', top: '8px', width: '15px', height: '15px', fill: '#67736b' }} viewBox="0 0 24 24">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
              </svg>
            </div>

            {/* Input Contraseña */}
            <div style={{ position: 'relative', borderBottom: '1.5px solid #d1d9d4' }}>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Contraseña"
                style={{
                  width: '100%',
                  border: 'none',
                  outline: 'none',
                  padding: '7px 28px 7px 4px',
                  fontSize: '13px',
                  color: '#252d29',
                  background: 'transparent',
                }}
              />
              <svg style={{ position: 'absolute', right: '4px', top: '8px', width: '15px', height: '15px', fill: '#67736b' }} viewBox="0 0 24 24">
                <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
              </svg>
            </div>

            {/* Botón Píldora */}
            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: '8px',
                padding: '11px',
                borderRadius: '24px',
                background: '#1c5547',
                color: '#ffffff',
                fontWeight: 600,
                fontSize: '14px',
                border: 'none',
                cursor: loading ? 'not-allowed' : 'pointer',
                boxShadow: '0 4px 12px rgba(28, 85, 71, 0.3)',
              }}
            >
              {loading ? 'Creando cuenta...' : 'Completar Registro'}
            </button>

            <p style={{ textAlign: 'center', fontSize: '12px', color: '#67736b', margin: '2px 0 0' }}>
              ¿Ya tienes cuenta?{' '}
              <button
                type="button"
                onClick={() => { setIsRegister(false); setError(null); }}
                style={{ background: 'none', border: 'none', color: '#1c5547', fontWeight: 700, cursor: 'pointer', padding: 0 }}
              >
                Inicia sesión
              </button>
            </p>
          </form>
        </div>

        {/* ================= PANEL CORTE DIAGONAL ANIMADO ================= */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: isRegister ? '0' : '50%',
            width: '50%',
            height: '100%',
            background: 'linear-gradient(135deg, #12382f 0%, #1c5547 100%)',
            clipPath: isRegister
              ? 'polygon(0 0, 100% 0, 80% 100%, 0 100%)'
              : 'polygon(20% 0, 100% 0, 100% 100%, 0 100%)',
            transition: 'all 0.6s cubic-bezier(0.68, -0.55, 0.27, 1.55)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '40px 30px',
            boxSizing: 'border-box',
            color: '#ffffff',
            textAlign: 'center',
            zIndex: 20,
          }}
        >
          {isRegister ? (
            <div style={{ maxWidth: '240px' }}>
              <h2 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 12px', letterSpacing: '0.5px' }}>
                ¡ÚNETE A REVIEWIQ!
              </h2>
              <p style={{ fontSize: '13px', lineHeight: 1.6, opacity: 0.9, margin: '0 0 24px' }}>
                Regístrate para calificar empresas y observar el impacto en el Semáforo de Experiencia.
              </p>
              <button
                type="button"
                onClick={() => setIsRegister(false)}
                style={{
                  padding: '9px 26px',
                  borderRadius: '24px',
                  background: 'transparent',
                  border: '2px solid #ffffff',
                  color: '#ffffff',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'background 0.2s',
                }}
              >
                Iniciar Sesión
              </button>
            </div>
          ) : (
            <div style={{ maxWidth: '240px' }}>
              <h2 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 12px', letterSpacing: '0.5px' }}>
                ¡BIENVENIDO!
              </h2>
              <p style={{ fontSize: '13px', lineHeight: 1.6, opacity: 0.9, margin: '0 0 24px' }}>
                Accede a tu cuenta para gestionar sincronizaciones de Google Play Store y publicar análisis.
              </p>
              <button
                type="button"
                onClick={() => setIsRegister(true)}
                style={{
                  padding: '9px 26px',
                  borderRadius: '24px',
                  background: 'transparent',
                  border: '2px solid #ffffff',
                  color: '#ffffff',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'background 0.2s',
                }}
              >
                Crear Cuenta
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}