# MODELOS.md — Coste, routing y telemetría de modelos por fase

> 📖 **Guía de coste, no una regla sellada.** Complementa `INICIO_PROYECTO.md` con
> el criterio de qué modelo usar en cada fase y cómo dejar constancia del gasto.
> El objetivo del harness es "contexto mínimo = coste mínimo"; este documento lo
> hace medible.

## 1. Routing por fase (barato en mecánica, fuerte en razonamiento)

| Fase | Tipo de trabajo | Modelo sugerido |
|---|---|---|
| M0–M1 | Lectura de PRD + entrevista | Estándar |
| M2 | Redacción de `SPEC.md` (razonamiento denso) | **Fuerte** |
| M3 | Trocear el plan en fases | Estándar |
| F0–Fn (mecánicas) | Bootstrap, datos, plumbing | **Barato** |
| Fn (lógica compleja) | Algoritmos, integraciones delicadas | Estándar/Fuerte según criterio |

Regla práctica: **el modelo barato basta mientras la fase no requiera razonar
sobre diseño o seguridad**; sube de nivel solo cuando la tarea lo exija y
regístralo en el checkpoint.

## 2. Snapshot de coste por fase

Al cerrar una fase, anota en su checkpoint (junto a la evidencia cruda) una línea
de coste para que quede rastreable:

```
- **F2:** Backend core validado. · Modelo: gpt-4o-mini · Tokens: ~42k · Coste est.: ~$0.03
    ```
    $ pytest -q
    18 passed in 3.2s
    ```
```

`task_generator.py --stats` resume el estado global (fases, checkpoints,
aprobaciones, sellos, snapshots). El coste agregado por fase se puede consolidar
periódicamente en `DECISIONS.md` (sección `## Costes`).

## 3. Qué registrar

- **Modelo** usado en la fase (identificador y proveedor).
- **Tokens** de entrada/salida aproximados.
- **Coste** estimado (o "no medido" si no lo tienes).

No es un requisito de cierre: es una práctica de gobernanza de coste. Si no lo
registras, la fase cierra igual; lo importante es que el dato no se invente.
