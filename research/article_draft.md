# Cien millones no son entropía: lo que FulcrumSec revela sobre los DNI hasheados

## SHA-256 no está roto. Esa es precisamente la mala noticia.

Durante años se ha repetido una idea tranquilizadora: si un identificador
personal no se guarda en claro, sino convertido en una cadena SHA-256, el dato
queda protegido.

La frase suena técnica. El resultado ocupa 64 caracteres hexadecimales. El
algoritmo es sólido. Y, sin embargo, la protección puede ser prácticamente
nula.

No hace falta romper SHA-256. Basta con probar todas las entradas posibles.

El último informe trimestral de GRIT, el equipo de inteligencia de GuidePoint
Security, describe un caso operativo de FulcrumSec que permite ver el problema
completo. Lo novedoso no es que una IA encontrara una vulnerabilidad para
entrar. Según la evaluación de GRIT, el grupo utilizó un LLM después de la
exfiltración, cuando ya tenía en sus manos una base de datos de producción
compleja.

La IA resolvió el problema que aparece después de robar terabytes: entender qué
se ha robado, cómo se relaciona y cuánto daño permite causar.

## Del volcado de datos al paquete de identidad

GRIT incluye una recreación saneada de la explicación que FulcrumSec habría
utilizado durante la negociación. Hay que ser precisos: el documento la
presenta como una evaluación de GRIT y como una recreación con campos
redactados, no como un volcado forense íntegro de prompts y respuestas.

Aun así, la secuencia es reveladora.

Primero, localizar una tabla de staging que contenía el identificador primario
en claro, junto con nombres, fechas de nacimiento, domicilios y una clave de
enlace.

Segundo, seguir esa clave. El mismo valor aparecía en decenas de tablas. Una
consulta permitía saltar desde una persona a documentos de identidad, cuentas
bancarias, correos, teléfonos, historial financiero y notas.

Tercero, recuperar las copias del identificador almacenadas como SHA-256. El
identificador tenía pocos dígitos y, por tanto, pocos millones de valores
posibles. La comunicación recreada afirma que se revirtieron millones en
minutos.

Cuarto, deshacer una ofuscación por sustitución de caracteres que se presentaba
como protección adicional.

El resultado no era una colección de tablas. Era un paquete de identidad
completo.

Aquí aparece el primer cambio introducido por la IA. Un LLM no necesita
debilitar el cifrado. Le basta con leer esquemas, nombres de columnas,
distribuciones, consultas y fragmentos de código; inferir relaciones; proponer
joins; identificar las representaciones débiles; y traducir todo eso a una
narrativa de impacto.

La IA no redujo la entropía del dato. Redujo la fricción del atacante.

## El DNI español cabe en 26,6 bits

El caso español hace que el error sea imposible de disimular.

La Agencia Tributaria define el NIF general de una persona española como ocho
dígitos, incluidos posibles ceros iniciales, y una letra de control. El
Ministerio del Interior publica el algoritmo: se divide el número entre 23 y el
resto determina la letra.

Por tanto, la letra no añade incertidumbre. Una vez conocidos los ocho dígitos,
la letra está determinada.

El espacio máximo es:

`100.000.000 = 10^8 ≈ 2^26,6`

Aplicar SHA-256 produce una salida de 256 bits, pero no convierte 26,6 bits de
entrada en 256 bits de secreto. El atacante genera:

`SHA256("00000000T")`

`SHA256("00000001R")`

... y continúa hasta:

`SHA256("99999999R")`

Después compara esos resultados con los hashes robados. Si todos los registros
usan el mismo formato, una sola pasada sirve para todos ellos.

El NIE es todavía más explícito. Su formato ordinario utiliza X, Y o Z, siete
dígitos y otra letra determinista. El dominio sintáctico superior es de 30
millones de candidatos, aproximadamente 24,8 bits.

El número de la Seguridad Social comparte el problema de los identificadores
estructurados y los dígitos de control, pero no debemos hacer una falsa
equivalencia: su dominio es mayor y necesita una medición propia. Lo mismo
ocurre con el número de póliza, cuyo formato depende de cada entidad.

La regla no es “todo identificador se rompe igual”. La regla es “antes de llamar
protección a un hash, mida el dominio real, la normalización y el coste de
enumerarlo”.

## Lo probamos con datos sintéticos

Para no quedarnos en la teoría, construimos un laboratorio con doce identidades
completamente ficticias. Los nombres son etiquetas sintéticas, los correos
terminan en `.invalid` y ningún identificador se asocia a una persona real.

El laboratorio reproduce siete tablas operativas y varios patrones:

- Una copia en claro en staging.
- Una copia SHA-256 en la tabla principal.
- Una clave común para enlazar contactos, perfil financiero y notas.
- Una copia ofuscada mediante sustitución de caracteres.
- Un registro de credenciales protegido con una función lenta.
- Controles comparativos con sal por fila, HMAC y tokenización.

En una CPU x86_64 con nueve hilos, una única pasada de los 100 millones de
candidatos recuperó los doce hashes:

- 12 objetivos.
- 12 identificadores recuperados.
- 35,90 segundos.
- 2,79 millones de candidatos por segundo.
- Cero fallos de consistencia.

La PoC registra además dos caminos independientes: la enumeración funciona sin
la tabla de staging; la clave de enlace funciona sin revertir el hash cuando
staging forma parte de la extracción. Juntas muestran que el alcance queda
determinado por la copia y la relación más débiles, no por la columna mejor
protegida.

Otra pasada completa sobre un único objetivo tardó 32,92 segundos. Una prueba
con una sal global conocida permaneció en el mismo orden de magnitud. Las
diferencias entre ejecuciones son ruido de un entorno compartido; antes de
publicar una cifra comparativa definitiva repetiremos el benchmark en un
MacBook M1 y utilizaremos la mediana.

También calculamos el almacenamiento. Una tabla mínima con digest binario y
número ocupa unos 3,35 GiB. En CSV, con el hash hexadecimal y el NIF completo,
ronda 6,98 GiB antes de indexación. Cabe en un portátil corriente.

Ni siquiera es necesario guardarla. El ataque puede recorrer el dominio en
streaming y conservar solo las coincidencias.

El código, los datos sintéticos, las pruebas y los resultados forman parte de
una PoC reproducible.

## La sal no es lo mismo que el secreto

Aquí conviene evitar una corrección demasiado simple: “faltaba sal”.

Una sal global conocida impide reutilizar una tabla creada para otra sal, pero
no impide volver a recorrer los 100 millones de valores.

Una sal aleatoria por fila, almacenada junto al hash, sí cambia la economía del
ataque. Ya no se puede amortizar una sola pasada entre millones de registros.
Sin embargo, un objetivo concreto sigue teniendo el mismo dominio. La sal
reduce la escalabilidad del ataque masivo; no vuelve secreto el DNI.

Para mantener una relación determinista entre sistemas, una opción más sólida
es HMAC-SHA-256 con una clave de alta entropía, separada de la base de datos,
gestionada en KMS o HSM y derivada por contexto. Sin la clave, el atacante no
puede calcular los pseudónimos candidatos.

Si la clave se roba junto con los datos, la protección vuelve a caer.

Cuando no sea necesario conservar la vinculación matemática, un token aleatorio
y una tabla de correspondencia separada ofrecen un diseño distinto. La tabla
pasa a ser el secreto crítico.

Argon2id o scrypt pueden hacer cada intento mucho más caro, como ocurre con las
contraseñas, pero suelen encajar peor en búsquedas y joins. La arquitectura no
se elige con una receta universal. Se elige a partir del propósito, el adversario
y el riesgo.

## La AEPD ya había descrito exactamente este ataque

No estamos ante una interpretación exótica del RGPD.

El artículo 4.5 define la seudonimización como un tratamiento que impide atribuir
los datos a una persona sin información adicional, siempre que esa información
se mantenga separada y protegida.

El artículo 32 exige medidas apropiadas al riesgo y al estado de la técnica. La
seudonimización aparece como una medida posible, no como una etiqueta que
convierta cualquier transformación en protección suficiente.

El considerando 26 pide valorar los medios razonablemente probables de
identificación, incluidos coste, tiempo y tecnología disponible.

Y la AEPD ya lo había explicado. El Dictamen 05/2014 del antiguo Grupo de
Trabajo del artículo 29 utiliza precisamente el ejemplo de aplicar una función
hash a un número de identificación nacional. Si se conoce el rango, se calculan
todos los valores y se comparan con el conjunto de datos. El mismo documento
advierte de que una sal conocida tampoco elimina necesariamente la
reidentificación por medios razonables.

ENISA llega a la misma conclusión técnica: el hash simple es una técnica débil
de seudonimización frente a fuerza bruta y diccionarios; una función MAC con
clave ofrece una protección mucho mayor mientras la clave permanezca separada.

Por eso conviene afinar el lenguaje. No todo informe que use la palabra
“seudonimizado” contiene una mentira deliberada. Pero si una EIPD, un análisis
de riesgos, un RAT o una auditoría atribuyen una reducción material de riesgo a
`SHA256(DNI)` sin analizar entropía, normalización, vinculación y enumeración,
su conclusión técnica es insostenible.

Y bajo un modelo de responsabilidad proactiva, una conclusión insostenible no
es un detalle semántico.

## Cuando el atacante conoce mejor tus datos que tú

Esta es la parte más importante para un comité de dirección.

El atacante puede usar IA para presentar, en pocas horas, un mapa de tablas,
claves, personas, categorías de datos, relaciones y consecuencias. La
organización, mientras tanto, inicia una carrera regulatoria.

El RGPD establece una ventana de hasta 72 horas para notificar a la autoridad
de control cuando corresponda. NIS2 fija una alerta temprana de 24 horas y una
notificación de 72 horas para incidentes significativos. A fecha de este
artículo, España todavía no había notificado su transposición completa y la
Comisión Europea la remitió al TJUE el 8 de julio de 2026, por lo que el alcance
nacional debe formularse con precisión.

DORA, directamente aplicable a las entidades financieras de su ámbito, exige
clasificar incidentes con criterios que incluyen pérdida de confidencialidad,
clientes afectados, criticidad e impacto económico. Su normativa de desarrollo
sitúa la notificación inicial dentro de cuatro horas desde la clasificación
como grave y, como máximo, 24 horas desde el conocimiento.

Ninguna de esas obligaciones puede cumplirse bien con un inventario que solo
existe en PowerPoint.

Si el actor que te extorsiona sabe antes que tú qué clave enlaza tus bases, qué
copias están en claro, qué hashes se pueden enumerar y cuántas personas quedan
expuestas, no tienes únicamente un problema criptográfico.

Tienes un problema de gobierno de la información.

## Tres preguntas para la próxima reunión

1. ¿Sabemos qué clave permite enlazar todas nuestras tablas y quién puede
   utilizarla?
2. ¿Qué identificadores de dominio reducido conservamos con transformaciones
   deterministas sin un secreto separado?
3. ¿Nuestro inventario de información permite fundamentar una clasificación y
   una notificación en 24 o 72 horas, o tendríamos que reconstruirlo durante el
   incidente?

SHA-256 sigue siendo seguro.

Lo que ya no es defendible es usar su nombre para ocultar que nunca se midió el
espacio real del dato.

## Fuentes principales

- [GRIT Q2 2026 Ransomware & Cyber Threat Insights Report](https://www.guidepointsecurity.com/wp-content/uploads/2026/07/GRIT_Q2_2026_Ransomware__Cyber_Threat_Insights_Report.pdf)
- [AEPD: Introducción al hash como técnica de seudonimización](https://www.aepd.es/guias/estudio-hash-anonimidad.pdf)
- [WP29: Dictamen 05/2014 sobre técnicas de anonimización](https://www.aepd.es/documento/wp216-es.pdf)
- [ENISA: Pseudonymisation techniques and best practices](https://www.enisa.europa.eu/publications/pseudonymisation-techniques-and-best-practices)
- [Ministerio del Interior: cálculo del dígito de control NIF/NIE](https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/calculo-del-digito-de-control-del-nif-nie/)
- [Agencia Tributaria: composición del NIF de personas físicas](https://sede.agenciatributaria.gob.es/Sede/ayuda/manuales-videos-folletos/manuales-practicos/guia-practica-cumplimentacion-modelo-censal-036/anexos/anexo-01-solicitud-nif-documentacion-aportar/informacion-sobre-numero-identificacion-fiscal/composicion-nif/personas-fisicas.html)
- [RGPD](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
- [Directiva NIS2](https://eur-lex.europa.eu/eli/dir/2022/2555/oj)
- [Comisión Europea: estado de la transposición española de NIS2, 8 de julio de 2026](https://digital-strategy.ec.europa.eu/en/news/commission-refers-ireland-spain-france-and-netherlands-court-justice-failing-transpose-rules)
- [DORA](https://eur-lex.europa.eu/eli/reg/2022/2554/oj)
