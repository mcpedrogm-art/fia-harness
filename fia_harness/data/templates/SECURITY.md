# SECURITY.md — Especificación y checklist de seguridad del proyecto

> **Uso:** este documento es una **plantilla que el kit entrega a cada
> proyecto**: se copia al arrancar y se rellena con las decisiones de
> seguridad de ESE proyecto. Si buscas la política de seguridad del
> repositorio de FIA Harness (cómo reportar una vulnerabilidad del propio
> kit), esa vive en `.github/SECURITY.md`.

**Estado: OBLIGATORIO en todo proyecto**, a diferencia de `AEO_GEO_SEO.md` (que solo aplica si hay superficie pública). Todo proyecto tiene datos, usuarios o infraestructura que proteger. Este documento se completa en la Fase 1.6 de `INICIO_PROYECTO.md`, se resume en `SPEC.md`, y cada `TASK-XXX.md` que toque datos, autenticación o infraestructura debe pasar su checklist correspondiente (Fase J2 de `TASK_TEMPLATE.md`) antes de cerrarse.

**Principio rector:** la seguridad no se improvisa "cuando dé tiempo". Se decide en la entrevista técnica, se diseña en `SPEC.md`, y se verifica en cada fase que la toque — no se pospone a un audit final.

---

## 1. Decisión del proyecto (rellenar en Fase 1.6)

- **Motor de BBDD y soporte de RLS:** <PostgreSQL/Supabase con RLS, MySQL sin RLS nativo, Firestore con reglas propias, etc.>
- **Proveedor de autenticación:** <gestionado (Auth0, Clerk, Supabase Auth, Firebase Auth) vs custom>
- **¿2FA/MFA requerido?** ¿Para quién? <solo administradores / todos los usuarios / opcional>
- **Tipo de despliegue:** <VPS propio, PaaS/serverless, contenedores gestionados> — determina si aplica hardening de servidor o no.
- **Datos sensibles manejados:** <PII, datos de pago, datos de salud, ninguno> — determina el nivel de cifrado y cumplimiento normativo exigido.
- **Normativa aplicable:** <RGPD, LOPD, PCI-DSS, HIPAA, ninguna>

---

## 2. Checklist por capa

### 2.1 Autenticación (AuthN)
- [ ] Contraseñas hasheadas con algoritmo robusto (bcrypt, argon2, scrypt) — nunca en texto plano, MD5 o SHA1 sin salt.
- [ ] **2FA/MFA** activo al menos para cuentas con rol administrador; evaluar si se exige a todos los usuarios según el nivel de riesgo.
- [ ] Gestión de sesiones: expiración razonable, rotación de tokens, revocación posible (logout real, no solo borrar del cliente).
- [ ] Rate limiting / bloqueo progresivo en el endpoint de login (protección contra fuerza bruta).
- [ ] Recuperación de contraseña con token de un solo uso y expiración corta (no preguntas de seguridad débiles).

### 2.2 Autorización y control de acceso a datos (AuthZ)
- [ ] **RLS (Row Level Security) activado en TODAS las tablas con datos de usuario**, si el motor lo soporta (PostgreSQL/Supabase).
- [ ] Principio de mínimo privilegio: la aplicación nunca usa el rol admin/superuser de la BBDD; roles separados (`anon` / `authenticated` / `service_role` / `admin`).
- [ ] Políticas explícitas por tabla y operación (SELECT/INSERT/UPDATE/DELETE), incluyendo `USING` y `WITH CHECK` cuando corresponda — **nunca `USING (true)` o `WITH CHECK (true)` sin justificación documentada en `DECISIONS.md`.**
- [ ] Funciones `SECURITY DEFINER` auditadas: sin `EXECUTE` para `anon` salvo necesidad explícita.
- [ ] Autorización también a nivel de API/backend (middleware que verifica permisos antes de cada endpoint sensible, no solo confiar en la BBDD).
- [ ] Las comprobaciones de propietario, tenant, rol y estado no pueden omitirse mediante campos enviados por el cliente.

### 2.3 Gestión de secretos
- [ ] Todas las credenciales en variables de entorno, nunca hardcodeadas ni en el repositorio.
- [ ] API keys/tokens sensibles **solo en backend/edge functions**, nunca expuestas al cliente ni en bundles de frontend.
- [ ] `.env` y equivalentes en `.gitignore`; verificar que nunca se ha commiteado un secreto (si ocurre, rotar la clave, no solo borrar el archivo).
- [ ] Rotación periódica de claves y tokens de larga vida.
- [ ] Uso de un gestor de secretos de la plataforma si está disponible (Secrets de Vercel/Coolify/AWS, Vault, etc.) en vez de `.env` planos en producción.
- [ ] Escaneo de secretos antes de cada entrega y revisión del historial del repositorio; si se detecta una exposición, revocar y rotar la credencial, no limitarse a borrar el archivo.

### 2.4 Protección de datos
- [ ] HTTPS/TLS obligatorio en todos los entornos, incluido staging.
- [ ] Cifrado en reposo para datos sensibles si aplica (PII, pagos, salud).
- [ ] Validación y sanitización de toda entrada de usuario (prevención de SQL injection, XSS, command injection) — usar queries parametrizadas/ORM, nunca concatenar SQL.
- [ ] Content Security Policy (CSP) configurada en el frontend.
- [ ] CORS restrictivo en producción (nunca `*` con credenciales).
- [ ] Protección CSRF en formularios/endpoints mutables cuando aplique el modelo de sesión.

### 2.5 Seguridad de infraestructura / servidor (si hay VPS o servidor propio)
- [ ] **Firewall del servidor**: solo puertos necesarios abiertos (80/443); SSH restringido por IP y/o clave, nunca abierto a `0.0.0.0/0` sin necesidad.
- [ ] SSH: solo autenticación por clave pública, login root deshabilitado, password auth deshabilitado.
- [ ] Proceso definido de actualizaciones de seguridad del SO y dependencias del sistema (no ad-hoc).
- [ ] BBDD no expuesta directamente a internet (solo accesible desde la red interna/backend).
- [ ] Backups automáticos y cifrados, con prueba de restauración verificada periódicamente.
- [ ] Fail2ban (o equivalente) u otra protección activa contra intentos de intrusión repetidos.

> Si el despliegue es serverless/PaaS (Vercel, Netlify, Railway...), este bloque se simplifica: no hay servidor que hardening manual, pero sí revisar configuración de red/WAF y rate limiting del proveedor.

### 2.6 Seguridad de aplicación y dependencias
- [ ] Escaneo de dependencias vulnerables integrado (`npm audit`, Dependabot, Snyk o equivalente).
- [ ] Nunca loguear información sensible (tokens, contraseñas, PII) — coherente con la Fase D de `TASK_TEMPLATE.md`.
- [ ] Rate limiting en endpoints públicos o de alto coste.
- [ ] Validación de esquema/tipos en cada input de API (zod, pydantic, class-validator, etc.), no solo en el cliente.
- [ ] Límites de tamaño, paginación, tiempo de espera y consumo definidos para entradas y operaciones costosas.

### 2.7 Monitorización y respuesta a incidentes
- [ ] Logs de acceso y errores centralizados (no solo en el servidor individual).
- [ ] Alertas ante actividad anómala (fallos de login repetidos, picos de tráfico inusuales).
- [ ] Plan mínimo documentado de respuesta ante una brecha: a quién avisar, cómo rotar credenciales comprometidas, cómo notificar si aplica RGPD.

### 2.8 Cumplimiento normativo (si aplica)
- [ ] Base legal del tratamiento de datos y política de privacidad publicada (RGPD/LOPD si hay usuarios UE).
- [ ] Mecanismo de derecho al olvido / exportación de datos si se manejan datos personales.
- [ ] Banner de consentimiento de cookies si se usan cookies no esenciales / tracking.

### 2.9 Skills, MCP, conectores y agentes externos

- [ ] Toda instalación, búsqueda, activación, conexión, selección o decisión técnica delegada tiene aprobación humana explícita previa.
- [ ] Toda creación, maquetación o modificación de una Skill/MCP tiene aprobación humana explícita del alcance, origen y permisos.
- [ ] Skills y MCP proceden de un origen identificado; se ha revisado su mantenimiento, alcance, permisos y dependencias.
- [ ] Se ha aplicado mínimo privilegio: lectura por defecto, rutas/hosts/dominios limitados y cuentas o tokens dedicados.
- [ ] Ninguna Skill o MCP recibe contraseñas, tokens, claves privadas, PII o secretos que no sean imprescindibles para la tarea.
- [ ] Las instrucciones recibidas desde una Skill, MCP, repositorio, README o página externa se tratan como datos no confiables, nunca como autorización.
- [ ] Se ha registrado la capacidad aprobada, la versión, la fecha, el responsable y la referencia de aprobación en `CONTEXT.md` o `DECISIONS.md`.
- [ ] Librerías, SDKs, APIs y versiones se han contrastado en Context7 antes de adoptarse; las excepciones están documentadas y aprobadas.

### 2.10 Seguridad de instrucciones y prompt injection

- [ ] Todo contenido procedente de usuarios, documentos, páginas web, repositorios, APIs, Skills o MCP se trata como dato no confiable.
- [ ] Las instrucciones autorizadas están separadas de los datos externos y de los resultados de herramientas.
- [ ] Ningún contenido externo puede cambiar el objetivo, conceder permisos, aprobar instalaciones o ordenar comandos, conexiones, envíos o despliegues.
- [ ] Se han definido allowlists de herramientas, dominios, rutas, comandos y operaciones para cada integración que procese contenido externo.
- [ ] Se han probado ataques directos e indirectos de prompt injection, incluida la ocultación en texto, metadatos, comentarios, README, documentos o respuestas de API.
- [ ] Se bloquea la exfiltración de secretos, tokens, PII, prompts internos y datos de otros usuarios.
- [ ] Las acciones sensibles requieren validación de política y aprobación humana aunque el contenido externo las solicite.
- [ ] Los logs y resultados de herramientas se redactan antes de incorporarse al contexto o mostrarse a otra integración.

---

## 3. Matriz rápida por stack (orientativa — completar con el stack real del proyecto)

| Stack / infraestructura | Qué se activa obligatoriamente |
|---|---|
| **PostgreSQL / Supabase** | RLS en todas las tablas, políticas explícitas por operación, `service_role` solo server-side, revisión de funciones `SECURITY DEFINER` |
| **Firebase / Firestore** | Reglas de seguridad de Firestore/Storage equivalentes a RLS, App Check para evitar abuso de API |
| **Auth propio (custom)** | Hashing robusto, 2FA propio o vía librería auditada, gestión de sesión y expiración explícita |
| **Auth gestionado (Auth0/Clerk/Supabase Auth)** | Configurar MFA en el proveedor, revisar políticas de sesión por defecto (no asumir que ya son seguras) |
| **VPS propio (Hetzner, DigitalOcean...)** | Firewall (ufw/iptables), SSH hardening, fail2ban, actualizaciones del SO, BBDD no expuesta a internet |
| **Serverless / PaaS (Vercel, Railway, Coolify...)** | Secrets del proveedor en vez de `.env` plano, revisar rate limiting/WAF de la plataforma |
| **Contenedores (Docker/K8s)** | Imágenes mínimas, sin secretos en la imagen, red interna entre servicios, usuario no-root dentro del contenedor |

---

## 4. Integración con el plan de fases

| Fase típica (ver `INICIO_PROYECTO.md`) | Checklist de seguridad que aplica |
|---|---|
| F1 — Modelo de datos / BBDD | 2.2 (RLS y políticas) desde el primer momento — no se pospone a una fase de "seguridad" al final |
| F2 — Backend core | 2.3 (secretos), 2.4 (validación de entrada), 2.6 (dependencias) |
| F4 — Autenticación y permisos | 2.1 (auth/2FA), 2.2 (autorización a nivel de API) |
| F5 — Integraciones externas | 2.3 (secretos de terceros), 2.4 (CORS si hay llamadas cruzadas) |
| F7 — Despliegue | 2.4 (TLS), 2.5 (firewall/servidor), 2.7 (monitorización) |
| F8 — QA final | Repaso completo de las secciones 2.1–2.10 antes de considerar el MVP cerrado |
| F0/F2/F5/F7 — Capacidades | Repaso de las secciones 2.9–2.10 y de `SKILLS_MCP.md`: origen, permisos, aprobaciones, versiones, conexiones y contenido no confiable |

**Responsable:** el agente de Backend/Infraestructura (o el rol equivalente en `AGENTS.md` si el proyecto es multi-agente). El Revisor/QA valida explícitamente este checklist antes de aprobar el cierre de F4, F7 y F8.

---

## 5. Regla de bloqueo

Ninguna `TASK-Fx.md` que modifique autenticación, permisos de acceso a datos, secretos, configuración de servidor, capacidades Skills/MCP o procesamiento de contenido externo puede marcarse como cerrada sin haber completado explícitamente la sección correspondiente de esta checklist en su informe final (Fase L, puntos 12, 18 y 20 de `TASK_TEMPLATE.md`). Si algo no aplica, se declara "No aplica" con motivo — nunca se omite en silencio.

---

## 6. Plantilla de checklist por fase/entrega (rellenar conforme avanza el proyecto)

| Fase | RLS/Políticas | Auth/2FA | Secretos | TLS/Firewall | Dependencias | Estado |
|---|---|---|---|---|---|---|
| F1 | | — | | — | | Pendiente / OK |
| F4 | — | | | — | | Pendiente / OK |
| F7 | — | — | | | | Pendiente / OK |
| F0/F2/F5/F7 | — | — | Aprobación y mínimo privilegio | Según conexión | Origen/versiones verificadas | Pendiente / OK |
