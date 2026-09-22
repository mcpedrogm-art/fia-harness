"""Generación de los archivos de gobierno de un proyecto nuevo (Fase M0).

CONTEXT.md, PROGRESS.md y el workflow de CI `.github/workflows/harness.yml`.
La generación del estado (`progress.json`) vive en `generators.bootstrap` porque
depende del compilador de `core.state`.
"""

# Fases de proceso del harness: fuente única para PROGRESS.md Y progress.json.
# Las dos salidas se generan de estos datos, así que nacen sincronizadas.
PROCESS_PHASES = [
    {"id": "M0", "title": "",
     "objective": "Bootstrap del harness y lectura del PRD/MVP (Fase 0)",
     "deliverable": "Plantillas activas, carpetas creadas y CONTEXT.md con el resumen del PRD",
     "depends_on": [], "depends_on_notes": "—", "status": "done"},
    {"id": "M1", "title": "",
     "objective": "Entrevista de Descubrimiento Técnico (Fase 1)",
     "deliverable": "`SECURITY.md` y `AEO_GEO_SEO.md` completados; decisiones registradas en `CONTEXT.md`",
     "depends_on": ["M0"], "depends_on_notes": "", "status": "pending"},
    {"id": "M2", "title": "",
     "objective": "Especificación Técnica (Fase 2)",
     "deliverable": "`SPEC.md` redactado y aprobado explícitamente por el humano",
     "depends_on": ["M1"], "depends_on_notes": "", "status": "pending"},
    {"id": "M3", "title": "",
     "objective": "Plan de Fases de Ejecución (Fase 3)",
     "deliverable": "Tabla de fases `F0`-`Fn` añadida más abajo, derivada de `SPEC.md`",
     "depends_on": ["M2"], "depends_on_notes": "", "status": "pending"},
]

CHECKPOINT_M0_SUMMARY = ("Estructura del proyecto configurada con éxito. Archivos del harness "
                         "activos y mapeados en la raíz. Listos para iniciar la entrevista técnica (M1).")


def generate_context_file(root_dir, prd_path, metadata: dict):
    """Crea el archivo CONTEXT.md inicial y lo guarda en la raíz."""
    print("\n-> Generando archivo de control CONTEXT.md...")
    context_path = root_dir / "CONTEXT.md"

    if context_path.exists():
        print("   [.] CONTEXT.md ya existe en la raíz. Saltando generación para no sobreescribir.")
        return

    prd_reference = f"basado en `{prd_path.name}`" if prd_path else "creado desde plantilla vacía"
    unresolved = set(metadata.get("unresolved", []))
    confidence = metadata.get("confidence", {})

    def flag(campo: str, texto: str) -> str:
        level = (confidence.get(campo) or {}).get("level")
        method = (confidence.get(campo) or {}).get("method", "heurística")
        if level == "media":
            return (f"{texto}\n\n> ⚠️ **Confianza media** ({method}): sección detectada por "
                    f"heurística; revisar y confirmar antes de aprobar la Fase 1.")
        if level == "ninguna" or (level is None and campo in unresolved):
            return f"{texto}\n\n> ⚠️ **Sin confirmar:** no se detectó esta sección en el PRD; revisar y completar a mano antes de aprobar la Fase 1."
        return texto

    title = metadata.get("title") or "Nuevo Proyecto"
    features_md = "\n".join([f"*  [ ] {f}" for f in metadata["features"]]) if metadata["features"] else "*  [ ] _(sin detectar — completar a mano)_"
    out_scope_md = "\n".join([f"*  {o}" for o in metadata["out_of_scope"]]) if metadata["out_of_scope"] else "*  Ninguno declarado aún."

    context_content = f"""# CONTEXT.md — Resumen Vivo del Proyecto

**Proyecto:** {title}
**Estado:** Activo · Generado automáticamente {prd_reference}

## 1. Visión del Negocio
### Problema que resuelve:
{flag("problem", metadata['problem'])}

### Usuario Objetivo:
{flag("users", metadata['users'])}

## 2. Alcance del MVP (Must-Have)
{flag("features", features_md)}

## 3. Fuera de Alcance (Out of Scope)
{out_scope_md}

## 4. Decisiones Confirmadas (Fase 1)
*Este bloque será rellenado automáticamente por el Agente de IA al terminar la Entrevista Técnica (Fase 1).*
*   **Stack:** Pendiente de entrevista técnica.
*   **Base de datos:** Pendiente de entrevista técnica.
*   **Seguridad / Auth:** Pendiente de entrevista técnica.
*   **Visibilidad:** Pendiente de entrevista técnica.
*   **Modo de trabajo:** Pendiente de entrevista técnica (Completo / Lite — ver `QUICKSTART_LITE.md`).

## 5. Instrucción para el Agente / Prompt de Arranque
> **Instrucción de Ingeniería de IA:** Lee este archivo como el punto de inicio de verdad absoluto del proyecto. Tu primer paso es iniciar la **Fase 1: Entrevista de Descubrimiento Técnico** ejecutando las preguntas descritas en `INICIO_PROYECTO.md` para completar la configuración de `SECURITY.md`, `AEO_GEO_SEO.md` y redactar `SPEC.md`. No programes nada todavía.
"""
    with open(context_path, "w", encoding="utf-8") as f:
        f.write(context_content)
    print("   [+] Archivo CONTEXT.md generado con éxito.")


def generate_progress_file(root_dir):
    """Genera un archivo PROGRESS.md inicial en la raíz.

    Usa DOS espacios de nombres de fase, con el MISMO esquema de tabla
    (`Fase | Objetivo | Entregable | Depende de | Estado`) para que una tabla se
    pueda pegar literalmente dentro de la otra sin reformatear nada:

    - `M0`-`M3`: fases del PROCESO/harness (lectura de PRD, entrevista, SPEC.md,
      plan de fases). Son las mismas para cualquier proyecto y SÍ se conocen en el
      momento del bootstrap, así que se pre-rellenan aquí.
    - `F0`-`Fn`: fases de EJECUCIÓN del proyecto real (modelo de datos, backend,
      frontend...). Dependen por completo de `SPEC.md`, que todavía no existe en
      este punto — por eso NO se adivinan aquí. Se añaden en la Fase M3
      (`INICIO_PROYECTO.md`, sección "FASE 3 — Plan de Fases de Ejecución"),
      copiando la tabla que el agente redacta allí.

    `task_generator.py` solo genera `TASK-Fx.md` para códigos `F<N>` — las fases
    `M<N>` son pasos de descubrimiento/documentación, no tareas de código, y se
    ejecutan siguiendo `INICIO_PROYECTO.md` directamente.
    """
    print("-> Generando archivo de control PROGRESS.md...")
    progress_path = root_dir / "PROGRESS.md"

    if progress_path.exists():
        print("   [.] PROGRESS.md ya existe en la raíz. Saltando generación.")
        return

    process_rows = "\n".join(
        f"| {phase['id']} | {phase['objective']} | {phase['deliverable']} | "
        f"{', '.join(phase['depends_on']) if phase['depends_on'] else '—'} | "
        f"{'[x] Listo' if phase['status'] == 'done' else '[ ] Pendiente'} |"
        for phase in PROCESS_PHASES
    )

    progress_content = f"""# PROGRESS.md — Hoja de Ruta e Historial de Fases

**Fase activa:** M1

## Fases del Proceso (Harness — ver `INICIO_PROYECTO.md`)

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |
{process_rows}

## Fases de Ejecución del Proyecto (F0-Fn — se añaden en M3, derivadas de SPEC.md)

<!--
Al completar la Fase 3 (INICIO_PROYECTO.md), pega aquí la tabla de fases
resultante SIN cambiar el orden de columnas, añadiendo solo la columna Estado
(todas empiezan en "[ ] Pendiente"). Ejemplo de fila:
| F0 | Bootstrap del repo, tooling, linting, CI básico | Repo inicial funcionando | SPEC aprobado | [ ] Pendiente |
`task_generator.py` detecta automáticamente la primera fila F<N> pendiente de
esta tabla; no toca la tabla de fases M0-M3 de arriba.
-->

| Fase | Objetivo | Entregable | Depende de | Estado |
| --- | --- | --- | --- | --- |

## Checkpoints de Contexto Recientes
- **M0 (Bootstrap):** {CHECKPOINT_M0_SUMMARY}
"""
    with open(progress_path, "w", encoding="utf-8") as f:
        f.write(progress_content)
    print("   [+] Archivo PROGRESS.md generado con éxito.")


GITHUB_WORKFLOW = """\
# Generado por bootstrap.py (kit FIA Harness v3). bootstrap.py nunca lo sobrescribe:
# personalízalo libremente para tu stack. Los scripts de la raíz son fachadas finas
# que importan el paquete instalado; el gate de merge es `fia verify --strict-receipts`.

name: Harness — reglas de oro

on:
  push:
    branches: [main, master]
  pull_request:

jobs:
  estado:
    name: Gobernanza — estado, evidencia y procedencia (fia verify)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # receipt verify necesita los commits históricos (ADR-009)
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Instalar FIA Harness (los scripts son fachadas; requieren el paquete)
        run: python -m pip install fia-harness
      - name: Verificación (merge gate)
        run: fia verify --strict-receipts
      # Procedencia "trusted" (ADR-005): ejecuta tu suite con `fia run`, sube los
      # artifacts de evidence/ y adjunta el digest que publica la plataforma:
      #   - run: fia run -- <tu comando de tests>
      #   - uses: actions/upload-artifact@v4
      #     with: { name: fia-evidence, path: evidence/ }
      #   - run: fia evidence --ingest ci_artifact_manifest.json

  secretos:
    name: Sin secretos en el repositorio (regla 8)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  calidad:
    name: Tests y auditoría de dependencias (regla 7)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Detección del stack en TODO el repo (no solo la raíz): localiza el proyecto
      # Node/Python menos profundo y publica su carpeta. Si no hay stack, los pasos
      # avisan con ::warning:: — nunca se omiten en silencio (regla de oro nº2).
      - name: Detectar stack
        id: stack
        run: |
          find_dir() {
            git ls-files -z | tr '\\0' '\\n' \
              | grep -E "$1" | grep -vE "$2" \
              | awk -F/ '{print NF-1"\\t"$0}' | sort -n \
              | head -n1 | cut -f2- | xargs -r dirname
          }
          node_dir="$(find_dir '(^|/)package\\.json$' '(^|/)node_modules/')"
          py_dir="$(find_dir '(^|/)(pyproject\\.toml|requirements\\.txt)$' '(^|/)(node_modules|\\.venv|\\.git)/')"
          echo "node_dir=$node_dir" >> "$GITHUB_OUTPUT"
          echo "py_dir=$py_dir" >> "$GITHUB_OUTPUT"
          echo "Stack detectado — Node: ${node_dir:-ninguno} · Python: ${py_dir:-ninguno}"

      # --- Node ---
      - uses: actions/setup-node@v4
        if: steps.stack.outputs.node_dir != ''
        with:
          node-version: "20"
      - name: Instalar dependencias Node
        if: steps.stack.outputs.node_dir != ''
        working-directory: ${{ steps.stack.outputs.node_dir }}
        run: npm ci || npm install
      - name: Tests Node
        if: steps.stack.outputs.node_dir != ''
        working-directory: ${{ steps.stack.outputs.node_dir }}
        run: |
          if node -e "process.exit(require('./package.json').scripts && require('./package.json').scripts.test ? 0 : 1)"; then
            npm test
          else
            echo "::warning title=Regla 7::package.json sin script 'test' en '${{ steps.stack.outputs.node_dir }}': añade tests o personaliza este paso."
          fi
      - name: Auditoría Node (falla en nivel high o superior)
        if: steps.stack.outputs.node_dir != ''
        working-directory: ${{ steps.stack.outputs.node_dir }}
        run: npm audit --audit-level=high

      # --- Python ---
      - uses: actions/setup-python@v5
        if: steps.stack.outputs.py_dir != ''
        with:
          python-version: "3.11"
      - name: Instalar dependencias Python
        if: steps.stack.outputs.py_dir != ''
        working-directory: ${{ steps.stack.outputs.py_dir }}
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          if [ -f pyproject.toml ]; then pip install -e .; fi
      - name: Tests Python
        if: steps.stack.outputs.py_dir != ''
        working-directory: ${{ steps.stack.outputs.py_dir }}
        run: |
          if [ ! -d tests ]; then
            echo "::warning title=Regla 7::No hay carpeta tests/ en '${{ steps.stack.outputs.py_dir }}': añade tests o personaliza este paso."
          elif python -m pytest --version >/dev/null 2>&1; then
            pytest -q
          else
            python -m unittest discover -s tests -p "test_*.py" -v
          fi
      - name: Auditoría Python (falla en vulnerabilidades conocidas)
        if: steps.stack.outputs.py_dir != ''
        working-directory: ${{ steps.stack.outputs.py_dir }}
        run: |
          pip install pip-audit
          if [ -f requirements.txt ]; then pip-audit -r requirements.txt; else pip-audit; fi

      - name: Aviso si no hay stack detectable
        if: steps.stack.outputs.node_dir == '' && steps.stack.outputs.py_dir == ''
        run: echo "::warning title=Regla 7::No se detectó stack Node ni Python; personaliza o elimina el job 'calidad'."
"""


def generate_github_workflow(root_dir):
    """Emite .github/workflows/harness.yml: convierte las Reglas de Oro 5 (estado),
    7 (tests) y 8 (secretos/commit) en checks de merge mecánicos. Si el archivo ya
    existe, no se toca — la personalización del usuario manda."""
    workflow_path = root_dir / ".github" / "workflows" / "harness.yml"
    if workflow_path.exists():
        print("   [.] .github/workflows/harness.yml ya existe. No sobrescrito.")
        return
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(GITHUB_WORKFLOW, encoding="utf-8", newline="\n")
    print("   [+] CI de reglas de oro generado: .github/workflows/harness.yml")
    print("       (gitleaks + auditoría de dependencias + validación del estado en cada push/PR)")
