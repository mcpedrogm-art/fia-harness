# DESIGN_DIRECTION.md — Dirección UI/UX de la web del producto FIA Harness

Aplicado según `UI_UX_EXCLUSIVA.md` (v del kit 2.0.0). **Estado de aprobación:** la web se construyó por encargo directo del responsable en una sola iteración; se propusieron las tres direcciones, se recomendó y aplicó la A, y las otras dos quedan documentadas para alternar si el responsable no aprueba la recomendada.

---

## 1. Gate de entrada (completo antes de diseñar)

| Dato | Respuesta |
|---|---|
| Producto | FIA Harness v2.0.0: kit local (Markdown + 2 scripts Python sin dependencias) que convierte cualquier agente de IA en un proceso de ingeniería disciplinado, con reglas verificadas en CI |
| Usuario | Desarrollador individual o estudio pequeño hispanohablante que ya usa agentes de IA y les ha visto romper producción por falta de especificación |
| Acción principal | Entender el mecanismo de enforcement en <60 s y decidir arrancar: "Arranca en 4 pasos" |
| Conversión | Descarga/uso del kit (CTA a la sección de arranque y al repo); métrica: clics en CTA principal |
| Contenido real | Salidas reales capturadas del producto (demo e2e del 2026-09-06), cifras reales (49 tests, 0 dependencias, 8 reglas), estudio de mercado propio |
| Marca | Industrial-técnica, austera, autoridad por precisión; anti-códigos: gradientes púrpura SaaS, Inter/Roboto, screenshots falsos flotando, dark-mode genérico |
| Stack | Un único HTML autocontenido (CSS y JS embebidos, sin build, sin frameworks); fuentes vía Google Fonts con fallback de sistema |
| Entornos | Escritorio y móvil (360 px+), navegadores modernos; funciona sin red (fallback de fuentes) |
| Accesibilidad | WCAG AA: contraste ≥ 4.5:1 en texto, foco visible, navegación por teclado, `prefers-reduced-motion` respetado, color nunca como único portador de estado |
| Restricciones | Nada de imágenes externas (SVG y CSS puro); nada de JS de terceros; español como idioma |

## 2. Tres direcciones Design DNA propuestas

### A. «ENCLAVAMIENTO» — recomendada ✅

- **Tesis visual:** la web se comporta como un enclavamiento ferroviario: nada avanza sin luz verde mecánica.
- **Metáfora:** el interlocking ferroviario — señales, trayectos, agujas. Es la metáfora exacta del producto: los trenes (agentes) no chocan porque el mecanismo lo impide, no porque alguien lo prometa. Además rima con el propio nombre (harness = arnés/amarre).
- **Sensación buscada:** control sereno, precisión industrial, confianza de manual técnico oficial. **A evitar:** urgencia comercial, postureo startup.
- **Gramática de layout:** columna única generosa (1080 px), divisores de sección como doble vía con traviesas, banda oscura "túnel" solo para la demostración de enforcement, datos como estaciones de un recorrido.
- **Tipografía:** Space Grotesk (display/cuerpo, geométrica industrial) + IBM Plex Mono (estados, comandos, etiquetas). Nada de Inter.
- **Paleta:** papel hueso `#F2EEE3` y tinta `#191813` como base (documento técnico impreso); verde señal `#1F9D57`, ámbar `#D99A06` y rojo `#C6433B` reservados EXCLUSIVAMENTE para estados; banda oscura `#17160F` con verde fósforo para el registro de CI.
- **Movimiento:** las tres señales del hero pasan de rojo a verde al entrar en viewport, escalonadas 400 ms, como una ruta que se libera. Fallback estático en verde.
- **Patrón distintivo:** la **señal de estado** (punto + etiqueta mono) como único portador de estado en toda la página, y la **vía** como divisor. Dos recursos propios que se repiten: reconocible sin efectos.

### B. «ACTA NOTARIAL» — descartada (documentada)

- **Tesis:** el contrato con la IA como acta notarial firmada y sellada.
- **Metáfora:** papel de fumar, tipografía serif de imprenta, sellos de cera roja "APROBADO", registro notarial de `APPROVAL-ID`.
- **A favor:** refuerza la idea de contrato social auto-ejecutable; muy memorable.
- **Por qué se descarta:** demasiado callada para la acción principal (demostrar mecanismo en <60 s) y su toque "heritage" podría leerse como producto jurídico, no de ingeniería. Buena para una futura página de la función de aprobaciones.

### C. «SALA DE CONTROL» — descartada (falla el anti-clon)

- **Tesis:** mission control: fondo oscuro total, fósforo verde, galgas y osciloscopios.
- **Por qué se descarta:** es la estética por defecto de toda landing de herramienta dev (dashboard genérico + dark mode cliché). Falla la regla de exclusividad nº2 ("no parece una plantilla SaaS sin razón de negocio") y la auditoría anti-clon. Se conserva solo la banda oscura aislada como contraste puntual dentro de la dirección A, donde tiene función real (el túnel del registro de CI).

**Combinación elegida:** Señal (mensaje claro con pocos elementos) + Instrumento (consulta y control), ejecutada con gramática editorial. Arquetipo de referencia: `Umbral` en la zona de CTA (la acción es empezar).

## 3. Arquitectura UX (recorrido por página)

Entrada (nav mínimo) → Promesa (H1 respuesta directa) → Prueba (registro real de CI bloqueando una trampa) → Exploración (método en 3 motores; reglas con dientes; cifras) → Contexto (paisaje competitivo honesto) → Objeciones (FAQ) → Acción (4 pasos) → Salida (footer con enlaces al kit y a llms.txt).

## 4. Sistema de movimiento (presupuesto y fallback)

| Elemento | Trigger | Objeto/propiedad | Duración | Fallback |
|---|---|---|---|---|
| Señales del hero | entrada en viewport | fondo del LED + aro | 480 ms escalonado 400 ms | verde estático |
| Secciones | entrada en viewport | opacidad + 12 px de elevación | 240 ms | visibles sin transform |
| Registro CI | sin animación de escritura | — | — | estático |
| Hover | mouse/focus | aro de señal + subrayado | 160 ms | sin transform en reduced-motion |

Reglas: `prefers-reduced-motion: reduce` desactiva todas las transiciones y deja los estados finales; ninguna animación bloquea interacción; coste < 3 kB de JS; ningún elemento se mueve solo de forma continua.

## 5. Tokens conceptuales (implementados en `:root`)

`color.surface.base/raised/deep` · `color.content.primary/muted/invert` · `color.line` · `color.signal.green/amber/red` (+ variantes glow para la banda oscura) · `type.display/body/label` · `space.section/gutter` · `radius.control/surface` · `motion.enter/state` · `shadow.ambient`.

## 6. Auditoría de originalidad (anti-clon)

- **Qué podría parecer genérico:** una landing dev con hero + features + FAQ. La diferenciación no está en el esqueleto sino en: metáfora del enclavamiento sostenida en todos los componentes (señales, vías, estaciones), paleta papel/tinta con señal cromática restringida a estados, tipografía no-Inter, y **salidas reales del producto** en vez de mockups.
- **Qué recordarían las referencias:** Spec Kit/Kiro usan dark-hero con degradado y mockup; aquí no hay degradados (el diseño funciona con todo apagado), ni screenshots, ni emoji decorativos en titulares.
- **Cómo se ha diferenciado:** la única zona oscura es el "túnel" de enforcement y existe porque el registro de CI vive en terminal; los estados se muestran siempre como señal (punto + etiqueta), nunca como checkmark genérico; el paisaje competitivo se muestra honesto (tabla comparativa con fortalezas rivales), algo que ninguna landing de la categoría hace.
- **Prueba de apagado:** todas las transiciones desactivadas y señales estáticas: la página sigue siendo totalmente comprensible y distintiva.

## 7. Integración con AEO_GEO_SEO.md (checklist aplicado)

`<h1>` único con respuesta directa; meta description única; JSON-LD `SoftwareApplication` + `FAQPage`; Open Graph; HTML semántico (landmarks, jerarquía h1→h3); FAQ en formato "respuesta directa primero" (AEO); bloques autocontenidos y cifras citables (GEO); `llms.txt` en la raíz de la web (GEO); `alt` en imágenes (SVG decorativos `aria-hidden`); contraste AA verificado por pares tinta/papel y verde-señal sobre papel hueso (4.6:1 en texto de señal con etiqueta en tinta).

## 8. Decisión pendiente de registro

Dirección **A «ENCLAVAMIENTO»** aplicada. Si el responsable prefiere la B («ACTA NOTARIAL») o una versión de la C con otra piel, la gramática de layout y los tokens están aislados para re-vestir sin tocar el contenido.
