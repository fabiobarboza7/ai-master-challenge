import { defineConfig, globalIgnores } from "eslint/config"
import nextVitals from "eslint-config-next/core-web-vitals"
import nextTs from "eslint-config-next/typescript"

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // eslint-plugin-react 7.37 quebra no ESLint 10 ao detectar a versão do React sozinho.
  { settings: { react: { version: "19.2" } } },
  globalIgnores([".next/**", "out/**", "build/**", ".vitest/**", "next-env.d.ts"]),
])

export default eslintConfig
