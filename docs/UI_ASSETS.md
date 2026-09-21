# UI_ASSETS.md — Pack de assets UI (v3.5)

> El kit **no distribuye contenido de terceros**: lleva el *mecanismo* (manifiesto +
> descarga verificada). El *contenido* lo aloja quien tenga derechos (p. ej. un
> bucket de Supabase self-hosted, un GitHub Release o cualquier estático con HTTPS).

---

## 1. Manifiesto `UI_ASSETS.json`

```json
{
  "version": 1,
  "assets": [
    {
      "path": "media/hero-aurora.mp4",
      "url": "https://cdn.ejemplo.com/fia-assets/v1/media/hero-aurora.mp4",
      "sha256": "<64 hex>"
    }
  ]
}
```

- `path`: ruta **relativa** dentro del proyecto (se rechazan absolutas y `..`).
- `url`: `http(s)://` o `file://` (para pruebas locales).
- `sha256`: hash del archivo; **fail-closed**: si no coincide, no se escribe nada.

## 2. Uso en un proyecto

```bash
fia assets fetch                 # usa UI_ASSETS.json del proyecto
fia assets fetch https://cdn.ejemplo.com/fia-assets/v1/UI_ASSETS.json
fia init --assets https://cdn.ejemplo.com/fia-assets/v1/UI_ASSETS.json   # init + pack
```

- **Opt-in**: nada se descarga si no ejecutas el comando (sin llamadas por defecto).
- **Idempotente**: si el archivo ya existe y su hash coincide, no se toca.
- **Atómico**: se descarga a `.part`, se verifica y luego se mueve a su sitio.
- Los assets quedan **autohospedados** en el proyecto (lo que piden las recetas:
  nada de hotlinks en producción). Para no inflar el repo: `media/` puede ir a
  `.gitignore` o usar Git LFS según el peso.

## 3. Publicar un pack (mantenedor)

```bash
fia assets manifest --dir-source ./pack --base-url https://cdn.ejemplo.com/fia-assets/v1
# → UI_ASSETS.json con path/url/sha256 de cada archivo
```

Sube `pack/` y `UI_ASSETS.json` a tu hosting (bucket público o URLs firmadas) y
comparte la URL del manifiesto. **Licencia:** publica solo material que puedas
redistribuir; el kit no incluye media de terceros.

## 4. Seguridad

- Sin traversal: el manifiesto no puede escribir fuera del proyecto.
- Sin ejecución: solo se descargan datos; no hay scripts ni instalación.
- HTTPS recomendado para el hosting; `file://` solo para pruebas.
- El manifiesto **no está firmado** (v1): si el hosting se compromete, un manifiesto
  malicioso podría servir otros binarios *con su hash*; por eso el pack debe vivir
  en infraestructura propia y sobre HTTPS. La firma del manifiesto es trabajo futuro.
