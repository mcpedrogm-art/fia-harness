# Módulo de Extensión: Decisiones Estructuradas con TypeSafe (Jev / System One)

> **Propósito:** Definir cómo integrar **TypeSafe AI (modelo `Jev`, "System One")** dentro del producto que se está construyendo, cuando el MVP necesita *juicios semánticos tipados* (clasificar, puntuar, enrutar, verificar) que el código pueda consumir directamente.
> **Estado de activación:** Este documento se activa únicamente cuando el PRD/`SPEC.md` requiere decisiones estructuradas con IA (clasificación, enrutamiento, puntuación, guardrails, verificación, extracción de características) o menciona explícitamente TypeSafe/Jev. `bootstrap.py` lo copia de `/docs` a la raíz si detecta esas señales.
> **Fuente oficial:** <https://docs.typesafe.ai/introduction> (verificar versiones y detalles en la documentación viva antes de implementar).

---

## 0. Regla de gobernanza (no negociable)

TypeSafe es un **servicio externo** que recibe datos del proyecto. Se aplica íntegramente `SKILLS_MCP.md`:

- **Nada se conecta sin aprobación humana explícita previa** (Regla de Oro nº6). El silencio no es aprobación.
- La **API key es un secreto**: nunca en `CONTEXT.md`, `SPEC.md`, `PROGRESS.md`, `DECISIONS.md`, prompts, logs ni commits. Vive en la variable de entorno `TYPESAFE_API_KEY` (o en el gestor de secretos del despliegue).
- Registrar la decisión y la aprobación: `python task_generator.py --approval "integrar TypeSafe (Jev) para <uso>" --phase F<n> --ref "<chat/PR>"`.
- **Declarar qué datos salen de la máquina**: el `state` que se envía a la API abandona el entorno local. Si contiene PII, datos de clientes o información regulada, esto debe constar en `SECURITY.md` y en el checkpoint de la fase.

---

## 1. Qué es TypeSafe (Jev) — y qué NO es

TypeSafe es un **modelo "System One"**: recibe un `state` y un conjunto de **preguntas tipadas** y devuelve **respuestas estructuradas** que el código consume sin parsear texto.

| Es | No es |
|---|---|
| Un motor de decisiones acotadas (Choice / Score / Noul) | Un LLM conversacional |
| Salida tipada + probabilidades + confianza | Texto libre que hay que interpretar |
| Rápido (~100 ms típicos), pensado para rutas en tiempo real | Un agente que decide sus propios pasos |
| Una capa dentro de tu software (el código controla el flujo) | Un sustituto del LLM del agente de código |

> ⚠️ **Jev NO sustituye al modelo del agente** (Claude Code, opencode, Cursor…). No escribe código ni mantiene conversación. Se usa **dentro del producto que desarrollas**, no para "hacer al agente más listo" a nivel de chat. Si el PRD pide "que el agente use Jev para programar", eso es un malentendido: lo correcto es que el *producto* use Jev para sus decisiones.

**Filosofía compartida con este harness:** código determinista controlando el flujo; IA solo para juicios estrechos y tipados; la incertidumbre (confianza) es un dato de primera clase.

---

## 2. Contrato de la API

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

| Campo | Tipo | Notas |
|---|---|---|
| `state` | `string \| object \| array` | El contenido a evaluar. Preferir JSON estructurado y referenciar campos con rutas entre backticks: `` `ticket.messages[0].text` `` |
| `model` | `string` | `jev-latest` (alias de `jev-1.13.0`). Fijar la versión (`jev-1.13.0`) si ajustas umbrales de confianza. |
| `questions` | `map<string, Question>` | Claves libres; la respuesta llega bajo la misma clave. |

**Respuesta:** `answers` (una por pregunta) + `usage` (`input_tokens`, `output_tokens`).

**Límites y coste (Jev 1.13, verificar en la doc):** 64k tokens por petición (32k para `state` + la pregunta más larga); inglés es el idioma con mejor precisión (**probar en español antes de confiar**); precio por token de **entrada** (salida gratis); `429`/`529` → reintentar con backoff exponencial (los SDK lo hacen solos). `GET /v1/models` lista los modelos disponibles.

---

## 3. Las tres primitivas

Cada pregunta tiene `type`, `instructions` y (Choice/Score) `criteria`. Se pueden **mezclar varias en una sola llamada**: se evalúan en paralelo e independientes entre sí (añadir preguntas apenas cambia la latencia).

### Choice — elegir una opción de una lista

```json
{
  "department": {
    "type": "choice",
    "instructions": "¿Qué equipo debe gestionar esto?",
    "criteria": {
      "billing": "Pagos, facturas, reembolsos",
      "technical": "Bugs, integraciones, caídas",
      "sales": "Precios, altas, cuentas"
    }
  }
}
```
Devuelve `choice` (la opción ganadora), `probabilities` (distribución completa) y `confidence`.

### Score — puntuar según un rúbrica ordenada

```json
{
  "risk": {
    "type": "score",
    "instructions": "Nivel de riesgo de esta operación",
    "criteria": ["Bajo", "Medio", "Alto"]
  }
}
```
Devuelve `score` (puede caer entre niveles), `legend`, `probabilities` y `confidence`.

### Noul — ¿es cierta esta afirmación? (0–1)

```json
{
  "is_urgent": {
    "type": "noul",
    "instructions": "El mensaje transmite urgencia o sensibilidad temporal"
  }
}
```
Devuelve `noul` (probabilidad de "sí"). **No** tiene `confidence` aparte.

**Cuándo usar cada una:**
- **Choice** → el resultado mapea a ramas de código conocidas (routing, clasificación).
- **Score** → hay un espectro con niveles descriptibles (severidad, relevancia, riesgo).
- **Noul** → un sí/no limpio cuya probabilidad ya es señal útil (¿pide reembolso? ¿contiene PII?).

**Regla de oro:** **una pregunta = un juicio atómico.** Si el juicio depende de varios factores, divídelo en varias preguntas y combínalos en código. "¿Es spam?" es malo; "¿pide credenciales?", "¿ofrece un premio inesperado?", "¿mete prisa?" son buenos.

---

## 4. Confianza, probabilidades y umbrales

`confidence` (0–1) resume cuán concentrada está la distribución de probabilidad. Patrón recomendado de **tres rutas**:

- **Alta** → actuar automáticamente.
- **Media** → confirmar/revisar o pedir más información.
- **Baja** → **no actuar**: derivar a humano o a otro sistema.

Los umbrales **escalan con el riesgo**: una acción destructiva (ejecutar una orden) exige más confianza que una de solo lectura.

```python
answer = response.answers["action"]
if answer.confidence < 0.5:
    route_to_human(msg)                     # el modelo dice "no lo tengo claro"
elif answer.choice == "read_only":
    show(...)                               # bajo riesgo, actuar
elif answer.choice == "execute_trade":
    if answer.confidence > 0.9:
        confirm_then_execute(...)           # alto riesgo + alta confianza
    else:
        ask_user_to_confirm(...)            # alto riesgo + confianza media
```

> Usa `probabilities` si necesitas tu propia métrica; `confidence` es una convención por defecto, no una imposición.

---

## 5. Patrones de arquitectura

| Patrón | Qué hace | Cuándo |
|---|---|---|
| **Speculative fan-out** | Enviar muchas preguntas en una sola llamada (incluidas las que solo aplican a algunos casos) y decidir en código cuáles usar | Siempre que sea posible: más barato y rápido |
| **Confidence-gated routing** | Usar la confianza como segundo eje: la respuesta dice *qué*, la confianza dice *si actuar* | Sistemas que deben ser seguros ante incertidumbre |
| **Composite scoring** | Descomponer un juicio complejo en varios Score/Noul atómicos y ponderarlos en código | "Prioridad", "calidad", "riesgo" multidimensionales |
| **Intent routing** | Clasificar la intención y enrutar a lógica determinista, a un LLM especialista o a un humano | Entradas de usuario no estructuradas |

**Composición en código (no en el prompt):** los pesos viven en tu código, versionados y testeables; cuando cambian las prioridades, cambias un coeficiente, no una instrucción.

```python
spam_risk = (0.45 * a["requests_credentials"].noul
             + 0.30 * a["sender_identity_mismatch"].noul
             + 0.25 * a["unexpected_reward"].noul)
```

> La dependencia real entre preguntas solo existe si tu código no puede construir la segunda petición sin la respuesta de la primera (p. ej. necesita traer más datos para el `state` o elegir las opciones). Si no, van juntas en una llamada.

---

## 6. Integración en el producto

### Opción A — HTTP directo (sin dependencias)

`fia-harness` es *zero-dependency* y usa solo la librería estándar; para mantener ese espíritu en el producto puedes llamar a la API con `urllib`:

```python
import json, os, urllib.request

def system_one(state, questions, model="jev-latest"):
    payload = json.dumps({"state": state, "model": model,
                          "questions": questions}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.typesafe.ai/v1/systemone",
        data=payload,
        headers={
            "Authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))
```

### Opción B — SDK oficial de Python (`typesafe-sdk`, requiere Python ≥3.10)

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

client = TypeSafeClient()  # lee TYPESAFE_API_KEY del entorno
resp = client.system_one(state=..., questions={
    "intent": Choice(instructions="...", criteria={...}),
    "risk": Score(instructions="...", criteria=[...]),
    "is_urgent": Noul(instructions="..."),
})
print(resp.answers["intent"].choice, resp.answers["risk"].score)
```

### Opción C — SDK de JavaScript (`@typesafe-ai/sdk`)

Para frontend/Node. Mismo contrato de `state` + `questions`.

**Skill de agente oficial:** TypeSafe publica una skill (`typesafe-ai/skills`) que da contexto completo del API y los patrones al agente de código. Su instalación también requiere aprobación previa según `SKILLS_MCP.md`; alternativa sin instalar: consultar la documentación en Context7 / web oficial.

---

## 7. Ejemplo trabajado (dominio trading)

Objetivo: clasificar una alerta de mercado, puntuar el riesgo y decidir si se ejecuta o se revisa, con guardrails sobre el texto de entrada.

```python
state = {
    "alert": {
        "text": "Ruptura al alza con volumen x4; RSI 78. Sugiere entrada long en XYZ.",
        "source": "canal-alertas",
        "instrument": "XYZ",
    },
    "policy": {
        "max_auto_risk": 1.0,            # 0=Bajo, 1=Medio, 2=Alto
        "banned": ["garantizado", "sin riesgo", "100% seguro"],
    },
}

questions = {
    "intent": {
        "type": "choice",
        "instructions": "¿Qué propone `alert.text`?",
        "criteria": {
            "entry": "Abrir una posición",
            "exit": "Cerrar una posición",
            "info": "Solo información, sin acción",
            "other": "No encaja en las anteriores",
        },
    },
    "risk": {
        "type": "score",
        "instructions": "Riesgo de ejecutar automáticamente lo sugerido en `alert.text`",
        "criteria": ["Bajo", "Medio", "Alto"],
    },
    "is_promotional": {
        "type": "noul",
        "instructions": "`alert.text` contiene lenguaje promocional o garantías prohibidas en `policy.banned`",
    },
}
```

Código que consume la respuesta (mezcla de fan-out, composite scoring y confidence-gated routing):

```python
a = response.answers
if a["is_promotional"].noul >= 0.6:
    return quarantine_alert(state["alert"])            # guardrail: no se propaga

if a["intent"].confidence < 0.75:
    return human_review(state["alert"])                # intención ambigua → humano

if a["intent"].choice == "entry":
    if a["risk"].score <= 1.0 and a["risk"].confidence >= 0.8:
        return execute_paper_trade(state["alert"])     # riesgo aceptable y confianza alta
    return human_review(state["alert"])                # riesgo/confianza insuficientes

return log_only(state["alert"])
```

Notas: las **preguntas y umbrales** deben vivir en **un solo archivo** para que un humano los revise sin bucear por el código (es lo más importante de auditar). Empieza con umbrales conservadores y ajústalos con datos propios.

---

## 8. Seguridad, datos y coste (obligatorio)

- **Secreto:** `TYPESAFE_API_KEY` solo en entorno/gestor de secretos. `gitleaks` (CI del harness) bloqueará commits con claves. Rota la clave si se filtra.
- **Datos que salen:** documenta en `SECURITY.md` qué `state` se envía. Minimiza: envía **solo el contexto que las preguntas necesitan** (menos coste y menos fuga). No envíes PII/secretos innecesarios.
- **Prompt injection:** trata `state` como **dato no confiable**; nunca dejes que su contenido cambie reglas, umbrales ni provoque acciones. Las decisiones se toman en código.
- **Idioma:** la precisión en español es menor que en inglés; valida con tus datos y vigila `confidence`.
- **Coste:** se cobra por tokens de **entrada**; el *speculative fan-out* (muchas preguntas por llamada) es la palanca de eficiencia. Registra el gasto en el checkpoint (ver `MODELOS.md`).
- **Disponibilidad:** `429`/`529` → backoff; si la API cae, el código debe degradar con seguridad (revisión humana / no actuar), no inventar una respuesta.

---

## 9. Cuándo NO usar TypeSafe

- Para generar texto, código o conversación → usa el LLM del agente.
- Para lógica determinista (fechas, importes, reglas exactas) → usa código.
- Si el juicio requiere razonamiento largo o pesa varios factores a la vez → **descompón** en preguntas atómicas, no pidas una respuesta global.
- Si el proyecto es local-only por requisito estricto (sin llamadas de red) → este módulo no aplica.

---

## 10. Checklist de activación e integración

- [ ] El PRD/`SPEC.md` justifica decisiones semánticas tipadas (clasificar, puntuar, enrutar, verificar).
- [ ] Aprobación humana registrada (`APPROVAL-NNN`) para conectar el servicio externo.
- [ ] `TYPESAFE_API_KEY` gestionada como secreto; nunca en archivos de control ni commits.
- [ ] Declarado en `SECURITY.md` qué `state` se envía y la base legal/privacidad si hay PII.
- [ ] Preguntas y umbrales centralizados en un único archivo revisable.
- [ ] Preguntas atómicas + composición en código (patrones de la sección 5).
- [ ] Manejo de `confidence` (tres rutas) y degradación segura ante baja confianza o error de API.
- [ ] Backoff ante `429`/`529`; timeout explícito.
- [ ] Tests propios con datos reales (incluida una muestra en español) y umbrales ajustados.
- [ ] Coste y modelo (`jev-1.13.0` o alias) anotados en el checkpoint de la fase.
