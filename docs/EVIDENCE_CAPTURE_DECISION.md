# docs/EVIDENCE_CAPTURE_DECISION.md — Decisión: mecanismo de captura de evidencia

**Fase:** F4 (spike técnico) · **Fecha:** 2026-09-15 · **Estado:** decidido
**Bloquea:** el schema JSON de F5 (Evidence Engine). Esta decisión se toma antes de
escribirlo, como exige el plan v3.0-core.

---

## 1. Pregunta a decidir

¿Cómo captura FIA la **ejecución real** de un comando (p. ej. `pytest -q`)?

- **(a) Wrapper de ejecución:** `fia run -- pytest -q` captura stdout/stderr, exit
  code y timestamps directamente. Máxima fiabilidad; obliga al agente a usar un
  wrapper en vez de su shell.
- **(b) Lectura de artifacts de CI:** FIA lee logs/artifacts que el CI ya produjo.
  No invasivo; la validación local pierde la garantía que sí tiene el CI.

## 2. Spike realizado (prototipo mínimo, no producto)

**Entorno:** Windows, Python 3.11.15, sin dependencias externas (stdlib-only).
**Fixture:** proyecto mínimo con 2 tests que pasan (`demo_app.calc`) y 1 test que
falla (`extra/test_roto.py`), para observar corridas verdes y rojas.

### (a) Wrapper — record de ejecución

Comando: `python spike_run.py -- python -m unittest discover -s tests -q`

```json
{
  "command": ["python", "-m", "unittest", "discover", "-s", "tests", "-q"],
  "cwd": "...\\f4_spike\\fixture",
  "exit_code": 0,
  "started_at": "2026-09-15T16:04:12.998153+00:00",
  "finished_at": "2026-09-15T16:04:13.057603+00:00",
  "duration_s": 0.06,
  "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "stderr_sha256": "a4ca7fdb558038cc308b1fd6de2fe627fd62e102d98eec88dab94abaea5b29b0",
  "stdout_bytes": 0,
  "environment": { "python": "3.11.15", "os": "Windows-10-10.0.26200-SP0" }
}
```

Corrida roja (test que falla): `exit_code: 1`, `duration_s: 0.057`, y en el stream
correspondiente `FAILED (failures=1)`.

**Hallazgo inmediato del spike:** `unittest` escribe su informe en **stderr**, no en
stdout (`stdout_bytes: 0`). El wrapper captura ambos streams; cualquier verificación
futura debe mirar la **salida combinada** y nunca asumir un stream concreto.

### (b) Verificación desde artifacts (simulando CI)

El "CI" produce artifacts (`evidence.json`, `stdout.txt`, `stderr.txt`) y un
manifiesto con sus digests (simula el digest que publica la plataforma al subir un
artifact). La verificación comprueba la cadena
`claim → command → execution → result → artifact → hash`:

```text
  [PASS] artifact:evidence.json:hash==manifest 5ad3fe576844
  [PASS] artifact:stdout.txt:hash==manifest e3b0c44298fc
  [PASS] artifact:stderr.txt:hash==manifest a4ca7fdb5580
  [PASS] claim:stdout_sha256==artifact
  [PASS] claim:stderr_sha256==artifact
  [PASS] artifact:marca-de-ejecucion
  [PASS] artifact:resultado-coherente-con-exit

RESULT: PASS — 0 problema(s)
```

Con la corrida roja, la misma verificación da **PASS** (un `FAILED` es coherente con
`exit_code: 1`: la cadena verifica la ejecución, no el éxito).

### (b) Manipulación del artifact

Se editó `stderr.txt` cambiando `FAILED` por `OK` (fabricar un verde):

```text
  [FAIL] artifact:stderr.txt:hash==manifest f294798e2545
  [FAIL] claim:stderr_sha256==artifact
  [FAIL] artifact:resultado-coherente-con-exit

RESULT: FAIL — 3 problema(s)
```

## 3. Hallazgos

1. **Los runners escriben donde quieren** (unittest → stderr; pytest → stdout).
   Capturar y hashear **ambos streams** es obligatorio; la "marca de ejecución" se
   busca en la salida combinada.
2. **El wrapper captura bien**: argv, cwd, exit code, timestamps UTC, duración,
   hashes y tamaño de ambos streams, entorno (Python/SO). No captura: identidad de
   quien ejecuta, integridad del binario ni estado de red.
3. **La lectura de artifacts verifica la cadena completa** si existe un digest
   confiable: artifact ↔ manifiesto, claim ↔ artifact, resultado ↔ exit code.
4. **Límite fundamental (honesto):** en local todo es fabricable (record + logs +
   manifiesto). Sin un **ancla externa** (el digest que publica la plataforma CI),
   la verificación local detecta errores y ediciones posteriores, pero **no
   fabricación deliberada**. La distinción `local validation` vs `trusted CI
   validation` no es retórica: es la frontera de la garantía.
5. **Fricción:** el wrapper obliga al agente a cambiar su forma de ejecutar (roza
   la promesa de "no intermediar en cómo trabaja"); los artifacts no cambian su
   flujo pero requieren CI.

## 4. Decisión: híbrido

1. **Local (opcional):** `fia run -- <comando>` produce un record de ejecución
   (`source: "local-run"`). Mejora la confianza si el agente lo usa; **nunca es
   obligatorio**.
2. **CI (fuente de verdad):** el job ejecuta la suite y **publica artifacts**; el
   digest lo emite la plataforma. `fia verify` en CI valida la cadena contra ese
   digest (`source: "ci-artifact"`). El estado/evidencia local **no** se acepta como
   verdad en CI.
3. **Reglas:** (a) `verify` distingue explícitamente evidencia `local` de `trusted`;
   (b) solo la evidencia con ancla de CI cuenta como `trusted` para el merge gate;
   (c) sin wrapper ni artifacts, la evidencia es "existencia" (lo que ya hace v2.2)
   y **no** cuenta como procedencia.

**Justificación:** máxima fiabilidad donde importa (el merge) sin romper el flujo
del agente en local. Es exactamente el híbrido que el plan consideraba razonable.

## 5. Implicaciones para F5 (schema EV) — contrato mínimo

```json
{
  "id": "EV-001",
  "type": "test",
  "source": "local-run | ci-artifact",
  "command": ["python", "-m", "unittest", "discover", "-s", "tests", "-q"],
  "cwd": "...",
  "exit_code": 0,
  "started_at": "...", "finished_at": "...", "duration_s": 0.06,
  "stdout_sha256": "...", "stderr_sha256": "...",
  "artifacts": [{ "name": "stderr.txt", "sha256": "..." }],
  "environment": { "python": "3.11.15", "os": "..." }
}
```

- La **procedencia** se expresa como cadena de referencias por hash; los artifacts
  de CI se referencian por el digest del manifiesto.
- `trusted` **no** es un campo que el agente escribe: lo calcula `verify` (F6) según
  la fuente y el ancla.

## 6. Implicaciones para F6 / F7

- **F6:** el reporte PROVENANCE solo da PASS si la cadena cierra; evidencia local
  sin ancla se reporta como `local (no trusted)`, no como fallo ni como PASS pleno.
- **F7:** el `harness.yml` generado debe subir artifacts y pasar su digest a
  `fia verify`; el smoke de tampering (evidencia fabricada → FAIL) usará este
  mecanismo.

## 7. Reproducibilidad

Los prototipos son throwaway (directorio temporal del spike): `spike_run.py`
(wrapper), `spike_ci_manifest.py` (digests), `spike_artifact_check.py`
(verificación). El código de referencia del wrapper y del verificador queda descrito
en las secciones 2 y 3; el fixture son 3 archivos (`demo_app/calc.py`,
`tests/test_calc.py`, `extra/test_roto.py`). Comandos:

```text
cd fixture
python ..\spike_run.py -- python -m unittest discover -s tests -q
python ..\spike_ci_manifest.py
python ..\spike_artifact_check.py
python ..\spike_run.py -- python -m unittest discover -s extra -q   # corrida roja
python ..\spike_ci_manifest.py
python ..\spike_artifact_check.py
# tamper: reemplazar FAILED por OK en stderr.txt y repetir la verificación
```

## 8. Criterio de salida de F4

- [x] Ambas opciones prototipadas sobre un caso mínimo.
- [x] Decisión documentada y justificada **antes** del schema JSON de F5.
- [x] Validada con ejemplo end-to-end: PASS en verde, PASS en rojo (coherente) y
      FAIL tras manipulación del artifact.
