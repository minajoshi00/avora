/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_ANALYTICS_API?: string;
  readonly VITE_ANALYTICS_VIEW_KEY?: string;
  readonly VITE_ADMIN_PASSWORD?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
