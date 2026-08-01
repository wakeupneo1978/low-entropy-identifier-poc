# Matriz de afirmaciones y evidencia

Fecha de corte: 27 de julio de 2026.

| Afirmación | Categoría | Formulación publicable | Evidencia | Evitar |
| --- | --- | --- | --- | --- |
| FulcrumSec usó un LLM para analizar una base exfiltrada | Evaluación de GRIT | “GRIT evalúa que FulcrumSec procesó datos exfiltrados mediante un LLM no identificado” | GRIT Q2 2026, sección sobre IA | “Está forénsicamente demostrado qué modelo y prompts usaron” |
| El LLM generó instrucciones para enlazar identidades | Observación/evaluación de GRIT | “GRIT observó una salida que atribuye a asistencia de IA y que explicaba el enlace entre bases” | Informe GRIT y recreación saneada | Presentar la recreación como log original íntegro |
| Había una clave común en decenas de tablas | Parte de una recreación saneada | “La recreación publicada describe una clave compartida por numerosas tablas” | Informe GRIT | Atribuir el esquema a una víctima concreta |
| Se revirtieron millones de SHA-256 en minutos | Afirmación incluida en la recreación | “La comunicación recreada afirma que el actor revirtió millones; nuestra PoC prueba de forma independiente la viabilidad” | GRIT + benchmark propio | Tratar la cifra del actor como medición independiente de GRIT |
| Las contraseñas sí usaban hashing resistente | Afirmación incluida en la recreación | “La recreación sostiene que las contraseñas sí tenían un tratamiento resistente; si se confirmara, mostraría un control aplicado de forma desigual” | Informe GRIT | “La empresa fue negligente” sin hechos, estándar aplicable y análisis jurídico |
| El incidente anónimo era Novo Nordisk | No demostrado | No identificar a la víctima | El informe sanea identificadores; Security Now trata Novo como información adicional | Fusionar ambos casos |
| El DNI tiene un dominio superior de 100 millones | Hecho y derivación | “Ocho dígitos, incluidos ceros iniciales, más una letra determinista: 100 millones de entradas sintácticas” | AEAT + Ministerio del Interior | Contar la letra como 23 veces más entropía |
| El NIE tiene 30 millones de entradas sintácticas | Derivación documentada | “X/Y/Z + siete dígitos + letra determinista: hasta 30 millones” | Ministerio del Interior | Afirmar que los 30 millones han sido emitidos |
| El número de Seguridad Social es igual de fácil que el DNI | No demostrado | “Comparte estructura y dígitos de control, pero requiere un benchmark propio por su dominio mayor” | BOE: 2 provincia + 8 orden + 2 control | “Se revierte en el mismo tiempo” |
| Cualquier número de póliza tiene baja entropía | Generalización no válida | “Cada emisor debe medir su formato, secuencialidad y controles” | Diseño específico del emisor | Dar una cifra nacional universal |
| Una sal soluciona el problema | Falso sin contexto | “Una sal pública por fila evita amortización masiva, pero no impide la búsqueda dirigida; un secreto separado cambia el problema” | WP29, AEPD, ENISA, PoC | Confundir sal pública con clave secreta |
| HMAC resuelve todo | Incompleto | “HMAC eleva la protección si la clave es fuerte, separada, controlada y no cae en la misma extracción” | ENISA | Ignorar compromiso, reutilización o acceso a la clave |
| `SHA256(DNI)` no es seudonimización bajo ninguna circunstancia | Demasiado categórico | “Un hash determinista sin secreto puede producir un identificador, pero aporta una reducción de riesgo de atribución nula o muy débil frente a enumeración” | RGPD 4.5/32, AEPD, WP29 | Convertir una evaluación contextual en prohibición absoluta |
| Un RAT que lo declare está mintiendo | Requiere intención | “Si atribuye protección material sin analizar entropía y enumeración, su conclusión técnica es insostenible y puede fallar la responsabilidad proactiva” | RGPD 5.2, 25 y 32 | Afirmar dolo sin evidencia |
| Toda brecha debe notificarse a la AEPD en 72 horas | Inexacto | “Debe notificarse sin dilación y, cuando sea posible, antes de 72 horas, salvo que sea improbable un riesgo para derechos y libertades” | RGPD 33.1 | Omitir la excepción y el momento de conocimiento |
| NIS2 ya está plenamente transpuesta en España | Falso a la fecha de corte | “La Directiva fija 24/72 horas, pero España seguía sin notificar transposición completa el 8 de julio de 2026” | Comisión Europea | Presentar la Directiva como ley española completa y universal |
| DORA exige clasificar toda pérdida de datos | Contextual | “Las entidades financieras de su ámbito clasifican incidentes con criterios que incluyen pérdida de confidencialidad y criticidad” | DORA 18 y 19; Reglamentos 2024/1772 y 2025/301 | Aplicarlo a cualquier empresa |
| La IA rompió SHA-256 | Falso | “La IA ayudó a localizar y operacionalizar una debilidad de dominio; SHA-256 no fue criptográficamente roto” | Análisis técnico | Titulares de ‘IA rompe SHA-256’ |

## Regla editorial

Cada párrafo que describa el caso debe poder responder a una de estas etiquetas:

- **Hecho publicado**
- **Evaluación de GRIT**
- **Afirmación del actor**
- **Inferencia del autor**
- **Resultado de la PoC**

Si la etiqueta no está clara, el párrafo debe reescribirse.
