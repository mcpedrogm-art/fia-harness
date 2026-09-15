# UI_UX_EXCLUSIVA.md — Sistema de dirección UI/UX diferencial

**Propósito:** proporcionar a cualquier LLM un método repetible para diseñar una interfaz propia, memorable y útil al iniciar un proyecto. El sistema toma referencias de alto nivel —incluido el enfoque de bibliotecas de secciones, fondos, movimiento y contexto observado en Dínamo Sites—, pero genera una dirección visual original para cada proyecto.

**Alcance:** diseño de producto, arquitectura UX, lenguaje visual, componentes, motion, responsive, accesibilidad y criterios de revisión. No sustituye a `SPEC.md`, `SECURITY.md`, `SKILLS_MCP.md` ni a las decisiones de producto.

**Regla de originalidad:** no copiar prompts, textos, nombres, código, assets, composiciones reconocibles ni identidad visual de una referencia. Las referencias sirven para extraer principios y posibilidades, no para producir clones.

---

## 1. Qué se aprende del modelo de referencia

La web analizada organiza una biblioteca de recursos visuales alrededor de tres ideas aprovechables a nivel metodológico:

- **Secciones combinables:** héroes, landings, prueba social, precios, métricas, contacto, navegación y footer se tratan como piezas con una intención concreta.
- **Fondos con atmósfera:** el fondo no es decoración aislada; establece profundidad, contraste, ritmo y contexto para el contenido.
- **Prompt + contexto + revisión:** la guía propone elegir una base, contextualizarla con objetivo, stack y contenido real, hacer propios los assets, revisar escritorio/móvil y corregir una cosa cada vez.

En la revisión pública del 3 de septiembre de 2026, el catálogo mostraba 76 secciones, 22 prompts abiertos para copiar y 40 fondos. La taxonomía visible cubría, entre otros, héroes, landings, especificaciones, casos, testimonios, precios, métricas, calculadoras, contacto, navegación y cierres. Esto sugiere una biblioteca modular orientada a ensamblar recorridos, no una única plantilla de página.

La adaptación para este sistema añade una capa de diferenciación: antes de diseñar se construye un **Design DNA** propio y se verifica que la solución no dependa de patrones genéricos ni replique una referencia.

---

## 2. Gate de entrada

No se debe generar una UI definitiva hasta completar estos datos:

| Dato | Pregunta que debe responderse |
|---|---|
| Producto | ¿Qué es y qué problema resuelve? |
| Usuario | ¿Quién lo usa, en qué contexto y con qué nivel de experiencia? |
| Acción principal | ¿Qué debe poder hacer o entender el usuario en los primeros segundos? |
| Conversión | ¿Qué resultado medible debe producir la interfaz? |
| Contenido | ¿Qué textos, datos, imágenes, vídeos o estados reales existen? |
| Marca | ¿Qué personalidad debe transmitir y qué códigos visuales deben evitarse? |
| Stack | ¿Qué framework, sistema de estilos, componentes y capacidades de animación están disponibles? |
| Entornos | ¿Qué dispositivos, navegadores, tamaños y condiciones de red se soportan? |
| Accesibilidad | ¿Qué nivel de contraste, teclado, lector de pantalla, reducción de movimiento e idioma se exige? |
| Restricciones | ¿Qué no se puede cambiar por negocio, legalidad, seguridad o rendimiento? |

Si faltan datos críticos, el LLM debe declarar supuestos y pedir confirmación antes de fijar la dirección visual.

---

## 3. Motor Design DNA

El Design DNA es la decisión que hace que una interfaz sea reconocible como propia. Debe definirse en una ficha breve:

```text
Nombre interno de la dirección:
Tesis visual en una frase:
Metáfora o comportamiento central:
Sensación buscada:
Sensación que se quiere evitar:
Gramática de layout:
Tipografía y jerarquía:
Paleta y contraste:
Tratamiento de imagen / vídeo / datos:
Comportamiento del movimiento:
Patrón de interacción distintivo:
Componentes que se repiten:
Decisión de accesibilidad principal:
Presupuesto de rendimiento:
Tres referencias de principio, no de copia:
Prueba de originalidad:
```

El Design DNA debe contener al menos un elemento propio en cada eje:

1. **Composición:** retícula, ritmo, densidad, alineación y uso del espacio.
2. **Tipografía:** contraste, escala, ancho de columna y tratamiento de titulares.
3. **Color/material:** contraste, superficie, textura, luz y relación entre fondo y contenido.
4. **Movimiento:** qué se mueve, cuándo, con qué causa y cómo se detiene.
5. **Interacción:** gesto, navegación, feedback, estado vacío o forma de explorar.
6. **Contenido:** tono, estructura narrativa y forma de demostrar valor.

No basta con cambiar colores o tipografías: la diferencia debe aparecer también en la composición, el comportamiento o la narrativa.

---

## 4. Selección de arquetipo sin encasillar el proyecto

Se puede elegir un arquetipo inicial y combinarlo con un segundo. El arquetipo es una hipótesis, no una plantilla cerrada.

| Arquetipo | Útil cuando | Riesgo a controlar |
|---|---|---|
| Editorial | Hay narrativa, criterio, casos o contenido de autor | Ser bonito pero poco accionable |
| Instrumento | El usuario debe consultar, comparar, calcular o controlar | Convertirse en dashboard genérico |
| Archivo | Hay catálogo, portfolio, documentación o histórico | Exceso de navegación sin prioridad |
| Campo | El producto conecta con territorio, materia, comunidad o exploración | Decoración sin información suficiente |
| Laboratorio | Hay innovación, proceso, datos o experimentación | Jerga y animación sin comprensión |
| Señal | La propuesta debe transmitir una idea clara con pocos elementos | Minimalismo vacío |
| Secuencia | El valor aparece por pasos, estados o transformación | Forzar un storytelling lineal |
| Umbral | La acción principal es entrar, reservar, empezar o convertir | Fricción excesiva antes de la acción |

Ejemplo de combinación: `Instrumento + Editorial` para un producto B2B que necesita mostrar métricas con autoridad y contexto.

---

## 5. Arquitectura UX antes de la estética

La interfaz debe diseñarse como un recorrido. Para cada pantalla o página, definir:

1. **Entrada:** desde dónde llega el usuario y qué sabe ya.
2. **Promesa:** qué entiende en los primeros segundos.
3. **Prueba:** qué evidencia reduce la incertidumbre.
4. **Exploración:** qué puede comparar, descubrir o profundizar.
5. **Acción:** cuál es la siguiente acción principal.
6. **Feedback:** qué confirma éxito, progreso, error o espera.
7. **Salida:** qué ocurre al completar o abandonar el flujo.

### 5.1 Inventario mínimo de secciones

No se deben añadir secciones por imitación. Cada una debe tener una función:

| Sección | Pregunta de diseño |
|---|---|
| Hero | ¿Qué promesa se entiende sin explicación adicional? |
| Prueba | ¿Qué evidencia es más creíble para este usuario? |
| Beneficios | ¿Qué cambia en la vida o trabajo del usuario? |
| Método | ¿Cómo se hace visible el proceso? |
| Datos | ¿Qué cifra o comparación ayuda a decidir? |
| Casos | ¿Qué historia demuestra el resultado? |
| Precio | ¿Qué debe poder comparar sin fricción? |
| FAQ | ¿Qué objeción bloquea la acción? |
| CTA | ¿Qué acción corresponde a este momento del recorrido? |
| Footer | ¿Cómo se cierra la experiencia y se orienta la siguiente visita? |

---

## 6. Patrón de contenido para cada componente

Para no producir “cajas bonitas” sin intención, cada componente debe documentarse así:

```text
Nombre:
Objetivo UX:
Información que necesita:
Acción principal:
Estados: inicial / hover / focus / carga / vacío / error / éxito / deshabilitado
Reglas responsive:
Movimiento permitido:
Fallback sin movimiento:
Requisitos de accesibilidad:
Métrica o señal de éxito:
```

El contenido real debe entrar antes de cerrar la composición. Los textos ficticios, números inventados y placeholders largos distorsionan las decisiones de jerarquía.

---

## 7. Sistema de movimiento

El movimiento debe comunicar estructura, causa o estado. Para cada animación especificar:

- **Trigger:** entrada, scroll, hover, focus, cambio de estado, gesto o acción del usuario.
- **Objeto:** qué elemento se mueve.
- **Propiedad:** posición, escala, opacidad, color, máscara, profundidad u otra.
- **Duración y ritmo:** suficiente para percibirse sin retrasar la tarea.
- **Jerarquía:** qué se mueve primero y qué queda estable.
- **Interrupción:** cómo se detiene o se adapta a navegación rápida.
- **Fallback:** versión estática o reducida.
- **Accesibilidad:** respeto de `prefers-reduced-motion` y control de foco.
- **Coste:** impacto estimado en CPU, GPU, red y batería.

Reglas:

- No animar todo al mismo tiempo.
- No usar movimiento para esconder una jerarquía de contenido débil.
- No depender de vídeo remoto si una imagen, CSS o canvas controlado resuelve la intención.
- No bloquear la interacción mientras una animación termina.
- El movimiento distintivo debe ser escaso y reconocible, no un efecto aplicado a cada componente.

---

## 8. Prompt maestro para generar la dirección UI/UX

Usar este prompt después de completar el Gate de entrada. Debe adaptarse al LLM utilizado; no presupone un proveedor concreto.

```text
Actúa como director/a de diseño de producto, arquitecto/a UX y diseñador/a de sistemas visuales.

PROYECTO
- Nombre: <nombre>
- Producto y problema: <descripción>
- Usuario principal: <usuario>
- Acción principal y métrica de éxito: <acción/métrica>
- Contenido real disponible: <contenido>
- Stack y restricciones técnicas: <stack>
- Dispositivos, navegadores y rendimiento objetivo: <entornos>
- Requisitos de accesibilidad y normativa: <requisitos>
- Códigos de marca que deben conservarse: <códigos>
- Códigos visuales que deben evitarse: <anti-referencias>

REFERENCIAS
- Usa las referencias solo para extraer principios de composición, ritmo, claridad, movimiento o narrativa.
- No copies prompts, textos, nombres, código, assets, layouts reconocibles ni identidad visual.
- Si una referencia es demasiado dominante, propón una desviación clara antes de continuar.

PROCESO OBLIGATORIO
1. Resume el problema UX y las decisiones que todavía faltan.
2. Propón tres direcciones Design DNA realmente diferentes, variando composición,
   tipografía/material, movimiento e interacción; no cambies solo el color.
3. Para cada dirección indica: tesis, metáfora, layout, tipo de contenido,
   componentes, navegación, motion, accesibilidad, rendimiento, riesgos y por qué
   sería propia para este proyecto.
4. Recomienda una dirección y explica qué sacrifican las otras dos.
5. Detente y solicita aprobación humana de la dirección elegida.
6. Tras la aprobación, entrega la arquitectura UX, mapa de secciones, estados,
   Design Tokens conceptuales, reglas responsive y especificación de movimiento.
7. Sustituye placeholders por contenido real o marca claramente lo que falta.
8. Incluye una auditoría anti-clon: qué elementos podrían parecer genéricos,
   qué referencia podrían recordar y cómo se han diferenciado.

FORMATO DE SALIDA
A. Resumen del producto y riesgos UX
B. Tres direcciones Design DNA
C. Recomendación y decisión pendiente
D. Arquitectura UX aprobable
E. Sistema visual y de componentes
F. Motion system y fallback reducido
G. Responsive, accesibilidad y rendimiento
H. Auditoría de originalidad
I. Checklist de validación
```

---

## 9. Tokens conceptuales

Antes de convertir el diseño en código, definir tokens semánticos, no valores dispersos:

```text
color.surface.base
color.surface.raised
color.content.primary
color.content.muted
color.action.primary
color.feedback.success
color.feedback.warning
color.feedback.error
space.page.gutter
space.section.block
radius.control
radius.surface
type.display
type.heading
type.body
type.label
motion.enter
motion.interaction
motion.state
shadow.ambient
```

Los valores deben derivarse de la dirección visual aprobada y probarse con contenido real. No se debe crear un sistema de tokens enorme antes de conocer las pantallas necesarias.

---

## 10. Reglas de exclusividad

La dirección puede considerarse suficientemente propia cuando cumple lo siguiente:

- [ ] Tiene una tesis visual que se puede explicar en una frase.
- [ ] Cambia al menos tres ejes respecto de cualquier referencia dominante.
- [ ] Tiene un patrón de interacción o narrativa propio del producto.
- [ ] El contenido real determina la jerarquía, no al revés.
- [ ] No depende de nombres, textos, assets o código de terceros.
- [ ] No parece una plantilla SaaS, dashboard, landing de agencia o portfolio genérico sin una razón de negocio.
- [ ] El movimiento aporta significado y dispone de fallback.
- [ ] La marca se reconoce sin necesidad de añadir más efectos.
- [ ] La composición funciona sin degradados o animaciones si se desactivan.
- [ ] La propuesta ha sido revisada y aprobada por una persona antes de implementarse.

Si falla alguno de los tres primeros puntos, volver a la fase de direcciones y no pasar a implementación.

---

## 11. Validación visual y UX

La revisión debe ejecutarse con contenido real y en este orden:

1. Claridad de la promesa y de la acción principal.
2. Flujo completo: entrada, exploración, acción, feedback y salida.
3. Estados vacíos, carga, error, éxito y datos largos.
4. Teclado, foco visible, contraste, lectura semántica y reducción de movimiento.
5. Escritorio, móvil, touch, orientación y tamaños intermedios.
6. Rendimiento: peso de assets, carga inicial, vídeo, fuentes y animaciones.
7. Consistencia de tokens, componentes y copy.
8. Diferenciación: comparación contra las referencias sin convertirla en una competición estética.

Las correcciones se hacen de una en una, se registran y se vuelven a validar. No se cambia simultáneamente estructura, copy, color y motion sin poder atribuir el resultado.

---

## 12. Entregables de la fase de diseño

Antes de pasar a implementación deben existir:

- `DESIGN_DIRECTION.md` o una sección equivalente en `SPEC.md`.
- Design DNA aprobado.
- Mapa de pantallas y recorrido principal.
- Inventario de componentes y estados.
- Tokens conceptuales iniciales.
- Reglas responsive, accesibilidad y motion.
- Lista de assets propios, licencias y fallbacks.
- Auditoría de originalidad.
- Criterios de aceptación visual y UX.
- Aprobación humana registrada en `DECISIONS.md` o `PROGRESS.md`.

---

## 13. Relación con el resto del sistema

- `INICIO_PROYECTO.md` decide en qué fase se crea y aprueba la dirección.
- `SPEC.md` conserva la versión aprobada y sus criterios de aceptación.
- `TASK_TEMPLATE.md` aplica este recurso en las tareas que toquen UI, UX, contenido o assets públicos.
- `SKILLS_MCP.md` controla las Skills, MCP y herramientas usadas para investigar, prototipar o validar.
- `SECURITY.md` protege assets, cuentas, secretos, conexiones y datos de usuarios.
- `AEO_GEO_SEO.md` se aplica a páginas públicas cuando corresponda.

---

## 14. Fuentes y límites de la referencia

La inspiración metodológica se obtuvo de la página pública de Dínamo Sites, su biblioteca de secciones/fondos y su guía de seis pasos. Se han utilizado únicamente patrones de alto nivel para construir este método original. No se incorporan prompts, código, textos, nombres de producto ni assets de la web.

- https://dinamosites.com/
- https://dinamosites.com/fondos
- https://dinamosites.com/guia
