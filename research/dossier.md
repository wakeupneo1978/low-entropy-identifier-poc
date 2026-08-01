# Dossier de investigación

## Título de trabajo

**Cien millones no son entropía: lo que FulcrumSec revela sobre los
identificadores españoles hasheados**

Subtítulo: **La IA no debilitó SHA-256. Redujo la fricción necesaria para
encontrar, relacionar y explotar los datos ya robados.**

Fecha de corte de fuentes: 27 de julio de 2026.

## 1. Pregunta de investigación

¿Qué protección efectiva aporta aplicar SHA-256, sin un secreto separado, a un
identificador de dominio reducido y formato conocido, y qué cambia cuando un
actor de extorsión utiliza IA para interpretar un modelo de datos exfiltrado?

La pregunta contiene dos problemas diferentes:

1. **Problema criptográfico**: el digest tiene 256 bits, pero la entrada puede
   tener solo 26,6 bits de entropía.
2. **Problema de gobierno de datos**: el valor de una extracción no reside en
   cada tabla aislada, sino en la capacidad de encontrar las claves que permiten
   enlazarlas.

## 2. Tesis depurada

Durante años, muchas organizaciones han tratado el hash de un identificador
como si fuera una barrera de confidencialidad. El caso descrito por GRIT
muestra un escenario operativo en el que un actor de extorsión habría usado un
LLM para acelerar la interpretación de un esquema complejo y convertir una
extracción masiva en perfiles de identidad enlazados.

El caso español hace visible el error de diseño:

- El NIF basado en DNI tiene ocho dígitos y una letra de control determinista.
- El dominio sintáctico superior es de 100.000.000 valores.
- `log2(100.000.000) = 26,575` bits.
- Calcular `SHA-256` no añade entropía a la entrada.
- Una pasada completa permite comparar, de forma amortizada, todos los hashes
  de una extracción que utilicen la misma representación.

Por tanto, un análisis de riesgos, EIPD, RAT o informe de auditoría que atribuya
una reducción material del riesgo de atribución a `SHA256(DNI)`, sin secreto y
sin una prueba frente a enumeración, necesita ser revisado. La afirmación
adecuada no es que SHA-256 esté roto, sino que se está utilizando para un
objetivo que no puede cumplir por sí solo.

## 3. Qué observó GRIT y qué no debe exagerarse

El informe **GRIT Q2 2026 Ransomware & Cyber Threat Insights** incluye una
sección titulada *AI is an Enabler, but Not How You Would Think*. GRIT afirma
haber observado lo que evalúa como procesamiento de datos exfiltrados por
FulcrumSec mediante un LLM no identificado.

La evaluación se apoya en:

- La complejidad del análisis respecto a la capacidad previamente observada
  del grupo.
- El corto tiempo disponible durante la negociación.
- La precisión y calidad del lenguaje empleado por el actor.

El informe reproduce de forma saneada una explicación de cuatro pasos:

1. Una tabla de staging contenía el identificador primario en claro, junto con
   nombres, fechas de nacimiento, domicilios y una clave de enlace.
2. La misma clave aparecía en decenas de tablas y permitía alcanzar documentos,
   cuentas bancarias, correos, teléfonos y otros atributos.
3. Algunas copias del identificador estaban en SHA-256, pero el dominio
   reducido permitía crear una correspondencia por enumeración.
4. Otras copias empleaban una sustitución de caracteres reversible.

La formulación pública está redactada como **recreación** y contiene
marcadores como `[PRIMARY_IDENTIFIER]`, `[LINKING_KEY]` y `[X]`. No identifica
al afectado ni aporta artefactos forenses reproducibles. En consecuencia:

- Es correcto escribir “GRIT evalúa”, “GRIT observó indicios” o “la recreación
  incluida en el informe describe”.
- No es correcto presentar cada detalle del mensaje como una comprobación
  forense independiente.
- El caso anónimo no debe identificarse automáticamente con Novo Nordisk,
  youX u otra víctima mencionada en informaciones posteriores.

Esta cautela no debilita el argumento criptográfico, que puede probarse de
forma independiente.

## 4. El ángulo español

### 4.1 DNI/NIF

La Agencia Tributaria publica que el NIF general de una persona española tiene
nueve caracteres: ocho dígitos, que pueden comenzar por cero, y una letra de
control. El Ministerio del Interior publica que la letra se obtiene dividiendo
el número entre 23 y sustituyendo el resto conforme a una tabla fija.

Resultado:

- Entradas numéricas: `00000000` a `99999999`.
- Número de candidatos: 100.000.000.
- Letra: totalmente derivada de los ocho dígitos.
- Entropía máxima del formato: 26,575 bits.

Que algunos números no se hayan emitido reduce el conjunto real. Nunca lo
aumenta.

### 4.2 NIE

El Ministerio del Interior describe el NIE como X, Y o Z, seguido de siete
dígitos y una letra de control. X, Y y Z se sustituyen por 0, 1 y 2 para aplicar
el mismo algoritmo.

El dominio sintáctico superior es:

`3 × 10.000.000 = 30.000.000` candidatos, aproximadamente 24,84 bits.

### 4.3 Número de la Seguridad Social

Una norma publicada en el BOE describe el formato como doce dígitos: dos de
provincia, ocho de orden y dos de control. Comparte el problema conceptual de
un identificador estructurado y con control determinista, pero no debe
presentarse como un caso idéntico al DNI:

- Su dominio es mayor.
- Las reglas de asignación y normalización deben documentarse.
- El tiempo y almacenamiento requieren un benchmark específico.

### 4.4 Número de póliza

No existe un único formato nacional. Cada entidad puede introducir prefijos,
secuencias, longitud y controles diferentes. La conclusión depende del emisor.
El artículo puede usarlo como pregunta de auditoría, no como afirmación
universal.

## 5. La prueba de concepto

### 5.1 Diseño

El laboratorio genera doce identidades completamente sintéticas y siete
tablas:

- `staging_identity`: NIF en claro, clave común y demografía ficticia.
- `customer_core`: SHA-256 del NIF y la misma clave.
- `contact_details`: correo `.invalid`, teléfono y póliza ficticios.
- `financial_profile`: sustituto no válido de IBAN, banda de ingresos y score.
- `case_notes`: NIF sometido a una sustitución byte a byte y nota ficticia.
- `auth_users`: registro scrypt para contrastar una KDF lenta.
- `defended_identifiers`: sal pública por fila, HMAC ilustrativo y token.

El enumerador nativo:

- Genera los 100.000.000 de NIF posibles en formato canónico.
- Calcula SHA-256.
- Compara cada resultado con todos los objetivos.
- No necesita persistir una tabla para demostrar la recuperación.
- Registra hilos, tiempo, throughput, formato y coincidencias en JSON.

### 5.2 Resultados de esta ejecución

Entorno:

- Linux x86_64.
- 9 hilos lógicos disponibles.
- C optimizado con hilos POSIX y OpenSSL 3.
- Datos exclusivamente sintéticos.

Resultados:

| Prueba | Candidatos | Objetivos | Resultado | Tiempo |
| --- | ---: | ---: | ---: | ---: |
| SHA-256 sin sal | 100.000.000 | 1 | 1 recuperado | 32,923 s |
| SHA-256 con sal global conocida | 100.000.000 | 1 | 1 recuperado | 36,541 s |
| Reconstrucción multitabla | 100.000.000 | 12 | 12 recuperados | 35,900 s |

La diferencia de tiempo entre pasadas es ruido de una ejecución en un entorno
compartido. No demuestra una ventaja de rendimiento de la sal. La comparación
publicable deberá repetirse al menos cinco veces en el Mac M1 y usar mediana,
desviación o rango intercuartílico.

La pasada con doce objetivos demuestra la propiedad importante: el coste no es
doce veces el coste de un objetivo. Todos los hashes con la misma
transformación se comparan durante el mismo recorrido.

### 5.3 Tamaño de una tabla completa

Una representación mínima con digest binario de 32 bytes y número de 4 bytes
ocupa:

`100.000.000 × 36 = 3.600.000.000 bytes = 3,35 GiB`

Una representación CSV con hash hexadecimal, separador, NIF completo y salto
de línea ronda:

`100.000.000 × 75 = 7.500.000.000 bytes = 6,98 GiB`

Un índice de base de datos añadirá sobrecarga. La demostración no necesita
guardar esa tabla; una enumeración en streaming usa mucha menos memoria.

### 5.4 Dos vías de compromiso

El laboratorio separa dos ataques que pueden coexistir:

1. **Enumeración criptográfica**: recuperar el NIF a partir de
   `customer_core.nif_sha256`.
2. **Vinculación por arquitectura**: seguir `link_key` desde la copia en claro
   de staging hacia las demás tablas.

Si staging se exfiltra, el atacante ni siquiera necesita revertir el hash para
relacionar los datos. Si staging no se exfiltra, el hash sin secreto sigue
siendo recuperable. La seguridad queda determinada por la copia más débil
dentro del alcance del incidente.

## 6. Por qué “añadir una sal” no es una respuesta completa

La palabra “sal” cubre diseños con efectos distintos.

### Sin sal

`SHA256(DNI)`

Una única tabla o pasada sirve para cualquier organización que use la misma
normalización.

### Sal global conocida

`SHA256(sal_global || DNI)`

Evita reutilizar una tabla creada para otra sal, pero permite una nueva pasada
de 100 millones. Si la sal está en código, configuración o base de datos
exfiltrada, no es un secreto.

### Sal aleatoria por fila, almacenada junto al hash

`SHA256(sal_fila || DNI)`

Impide amortizar una sola pasada entre todas las filas. Un ataque dirigido
contra una fila sigue recorriendo el mismo dominio. Es una mejora económica,
no una garantía de irreversibilidad.

### HMAC con clave secreta

`HMAC-SHA256(clave_contexto, DNI)`

Sin la clave no es posible calcular pseudónimos candidatos. La clave debe:

- Tener alta entropía.
- Estar fuera del conjunto de datos.
- Residir idealmente en KMS o HSM.
- Rotarse mediante un diseño previsto.
- Derivarse por finalidad o contexto para evitar vinculación universal.
- Tener acceso, uso, tasa y auditoría controlados.

Si la clave se exfiltra junto con la base de datos, el dominio vuelve a ser
enumerable.

### Tokenización

Un token aleatorio no derivado matemáticamente del DNI evita la enumeración. La
tabla de correspondencia se convierte en el activo crítico y debe estar
separada y fuertemente controlada.

### Funciones lentas

Argon2id, scrypt y otras KDF elevan el coste por candidato. Son apropiadas para
contraseñas, pero pueden encajar mal con búsquedas y joins deterministas. Para
identificadores empresariales, HMAC con separación de claves o tokenización
suelen ofrecer mejor equilibrio entre utilidad y protección.

## 7. Base regulatoria

### 7.1 RGPD

El artículo 4.5 define la seudonimización como un tratamiento que impide
atribuir los datos a una persona sin información adicional, siempre que esa
información figure por separado y esté protegida.

El artículo 32 exige medidas técnicas y organizativas apropiadas al riesgo,
teniendo en cuenta estado de la técnica, costes, naturaleza, contexto y riesgo.
La seudonimización es un ejemplo, no un salvoconducto automático.

El considerando 26 exige valorar medios razonablemente probables de
identificación, incluidos coste, tiempo y tecnología disponible. Un recorrido
de segundos o minutos encaja directamente en ese análisis.

El artículo 33 establece notificación a la autoridad de control sin dilación
indebida y, cuando sea posible, antes de 72 horas desde que el responsable
tiene constancia, salvo que sea improbable un riesgo para derechos y
libertades.

### 7.2 AEPD, WP29 y ENISA

La AEPD advierte que la adecuación del hash depende de la entropía del mensaje
y de la información vinculable.

El Dictamen 05/2014 del antiguo Grupo del artículo 29 utiliza expresamente el
ejemplo de aplicar una función hash a un número de identificación nacional:
cuando se conoce el rango, se calculan todas las entradas y se comparan los
resultados. También advierte que una sal no elimina necesariamente la
posibilidad de recuperar el valor por medios razonables.

ENISA considera el hash simple generalmente débil como técnica de
seudonimización por su exposición a fuerza bruta y diccionario. Presenta MAC,
y en particular HMAC, como técnica robusta mientras la clave no se comprometa.

En enero de 2025 el EDPB adoptó para consulta pública unas directrices sobre
seudonimización. Su versión pública indica que la transformación debe involucrar
información secreta de entropía suficiente y cita como contraejemplo aplicar
SHA-256 a identificadores conocidos. A julio de 2026 esa versión debe citarse
como texto de consulta, no como versión final consolidada.

### 7.3 NIS2 en España

El artículo 23.4 de la Directiva NIS2 establece:

- Alerta temprana dentro de 24 horas desde que se conoce un incidente
  significativo.
- Notificación dentro de 72 horas.
- Informe final, con carácter general, en un mes.

Sin embargo, a 27 de julio de 2026 España no había notificado la transposición
completa. La Comisión Europea anunció el 8 de julio de 2026 su remisión al
Tribunal de Justicia de la Unión Europea junto con Irlanda, Francia y Países
Bajos.

El artículo debe presentar el calendario como exigencia de la Directiva y
referencia operativa de preparación, no afirmar que cualquier empresa española
está hoy sometida directamente al régimen nacional completo de NIS2.

### 7.4 DORA

DORA es directamente aplicable a las entidades financieras de su ámbito. Su
artículo 18 obliga a clasificar incidentes según clientes afectados, duración,
extensión geográfica, pérdida de disponibilidad, autenticidad, integridad o
confidencialidad, criticidad del servicio e impacto económico.

El Reglamento Delegado 2025/301 concreta:

- Notificación inicial dentro de cuatro horas desde la clasificación como
  grave y, como máximo, 24 horas desde que se conoce.
- Informe intermedio dentro de 72 horas desde la notificación inicial.
- Informe final dentro de un mes.

Clasificar correctamente una pérdida de confidencialidad exige conocer qué
datos y funciones estaban en los activos afectados.

## 8. La asimetría de inventario

El hallazgo más relevante para gobierno no es que un atacante calcule hashes.
Es que el atacante puede llegar a entender la extracción antes de que la
organización entienda el incidente.

El LLM reduce el coste de:

- Inventariar tablas, columnas, formatos y volúmenes.
- Inferir relaciones a partir de nombres, claves y distribuciones.
- Localizar copias en claro, hashes, cifrados y ofuscaciones.
- Generar consultas de enlace.
- Clasificar datos por sensibilidad y jurisdicción.
- Convertir el inventario en una narrativa de impacto y presión.

La IA no reduce la entropía del identificador. Reduce la fricción analítica del
atacante.

Un defensor sujeto a ventanas de 24 y 72 horas necesita responder, con
evidencia:

- Qué activos fueron accedidos.
- Qué tablas y campos contienen.
- Qué transformaciones protegen cada copia.
- Qué clave permite relacionarlos.
- Cuántas personas y jurisdicciones están afectadas.
- Qué daño puede producir la combinación, no solo cada campo aislado.

Si esa respuesta se reconstruye manualmente durante la crisis, el inventario no
es un control operativo.

## 9. Tres preguntas para el comité de dirección

1. **¿Sabemos qué clave permite enlazar todas nuestras tablas y quién puede
   utilizarla?**
2. **¿Qué identificadores de dominio reducido conservamos con transformaciones
   deterministas sin un secreto separado?**
3. **¿Nuestro inventario de información permite fundamentar una clasificación
   y una notificación en 24 o 72 horas, o tendríamos que reconstruirlo durante
   el incidente?**

## 10. Siguiente fase experimental antes de publicar

1. Ejecutar cinco repeticiones completas en el MacBook Pro M1.
2. Registrar versión de macOS, CPU, compilador, OpenSSL, número de hilos y
   temperatura aproximada.
3. Publicar mediana, mínimo, máximo y throughput.
4. Repetir para:
   - ocho dígitos sin letra;
   - NIF completo;
   - sal global conocida;
   - tres sales por fila sobre un subconjunto documentado.
5. Implementar HMAC con clave fuera de la base y demostrar que la extracción no
   permite validar candidatos.
6. Simular dos alcances:
   - base operativa sin staging;
   - base operativa más staging y catálogo.
7. Ejecutar un ejercicio de inventario con cronómetro:
   - tiempo del atacante para generar un mapa;
   - tiempo del defensor para producir una ficha de notificación.
8. Someter la sección jurídica a revisión de un DPO o abogado especializado.
9. Consultar a GRIT si puede confirmar, sin revelar a la víctima:
   - si “recreación” preserva la secuencia real de los cuatro pasos;
   - qué evidencia distinguió asistencia de IA de trabajo humano;
   - si el benchmark de “millones en minutos” fue validado o procedía del actor.

## 11. Criterio de éxito

El trabajo será publicable cuando:

- Cada afirmación tenga categoría de hecho, evaluación, inferencia o resultado
  experimental.
- Todos los resultados puedan reproducirse sin datos reales.
- El código y el informe incluyan hashes de integridad.
- El benchmark del hardware publicado tenga varias repeticiones.
- El texto no confunda seudonimización con anonimización.
- La recomendación distinga sal, secreto, HMAC, KDF y tokenización.
- El estado de la transposición española de NIS2 esté actualizado el día de
  publicación.
