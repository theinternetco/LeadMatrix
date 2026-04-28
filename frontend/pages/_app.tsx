import '../styles/globals.css'
import type { AppProps } from 'next/app'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'

const PUBLIC_ROUTES = ['/', '/login']

export default function App({ Component, pageProps }: AppProps) {
  const router  = useRouter()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const token    = localStorage.getItem('lm_token')
    const isPublic = PUBLIC_ROUTES.some((r) => router.pathname === r)

    if (!token && !isPublic) {
      router.replace('/login')
    } else {
      setReady(true)
    }
  }, [router.pathname])

  // Don't flash protected content while redirecting
  if (!ready && !PUBLIC_ROUTES.some((r) => router.pathname === r)) return null

  return <Component {...pageProps} />
}
