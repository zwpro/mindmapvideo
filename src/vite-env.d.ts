/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_API_PREFIX: string
  readonly VITE_DEV_PROXY_TARGET?: string
  readonly VITE_APP_NAME: string
  readonly VITE_APP_ENV: 'development' | 'production' | string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
