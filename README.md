# Cien millones no son entropía

[English](README_EN.md) · [Metodología](research/dossier.md) · [Alcance ético](ETHICS.md)

[![CI](https://github.com/wakeupneo1978/low-entropy-identifier-poc/actions/workflows/ci.yml/badge.svg)](https://github.com/wakeupneo1978/low-entropy-identifier-poc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Synthetic data only](https://img.shields.io/badge/data-100%25%20synthetic-22c55e)](ETHICS.md)

Laboratorio reproducible que demuestra por qué aplicar SHA-256 de forma
determinista y sin un secreto separado aporta muy poca protección a un
identificador procedente de un dominio pequeño. El DNI/NIF español se utiliza
como caso de estudio: ocho dígitos y una letra de control determinista producen
100.000.000 de candidatos sintácticos, aproximadamente 26,58 bits.

> **El repositorio utiliza exclusivamente identidades sintéticas.** No contiene
> DNI obtenidos de personas reales, datos personales, material de filtraciones ni tablas
> precalculadas. No debe utilizarse para procesar información de terceros.

SHA-256 no está roto. La propiedad que se explora es distinta: si el atacante
puede enumerar todas las entradas posibles, puede calcular sus hashes y
compararlos con los valores extraídos. Una salida de 256 bits no convierte una
entrada predecible en un secreto de 256 bits.

![Portada: Cien millones no son entropía](research/portada_linkedin_cien_millones_entropia.jpg)

## Resultado reproducido

La PoC construye siete tablas sintéticas y tres caminos independientes de
atribución: enumeración del hash, unión mediante una clave estable y reversión
de una ofuscación débil. La ejecución base recuperó los 12 objetivos sintéticos
y reconstruyó 12 perfiles sin fallos de consistencia.

| Medición base | Resultado | Tiempo |
| --- | ---: | ---: |
| Un objetivo, dominio completo | 1/1 recuperado | 32,92 s |
| Doce objetivos y reconstrucción multitabla | 12/12 recuperados | 35,90 s |
| Un objetivo con sal global conocida | 1/1 recuperado | 36,54 s |

Son mediciones de referencia realizadas en Linux x86_64 con 9 hilos lógicos;
no son una promesa de rendimiento. El hardware, el software y la metodología
exactos están registrados en [`results/`](results/README.md).

## Reproducción rápida

Requisitos:

- Python 3.11 o posterior.
- GCC o Clang y `make`.
- OpenSSL 3 y sus cabeceras de desarrollo.
- Hilos POSIX, disponibles en Linux y macOS.

En Ubuntu/Debian:

```bash
sudo apt-get install build-essential libssl-dev pkg-config python3
```

En macOS con Homebrew:

```bash
xcode-select --install
brew install openssl@3 pkg-config python@3.12
export PKG_CONFIG_PATH="$(brew --prefix openssl@3)/lib/pkgconfig"
```

Compila y ejecuta las pruebas, incluida una integración limitada a un millón de
candidatos:

```bash
git clone https://github.com/wakeupneo1978/low-entropy-identifier-poc.git
cd low-entropy-identifier-poc
make clean test
```

Genera el laboratorio y ejecuta la reconstrucción completa:

```bash
python3 src/generate_lab.py --output lab/synthetic_identity.db
python3 src/run_reconstruction.py \
  --database lab/synthetic_identity.db \
  --cracker build/dni_sha256_enum \
  --output results/reconstruction_local.json \
  --limit 100000000
```

Para una comprobación rápida, cambia el límite a `1000000`. Esa prueba solo
recupera los objetivos situados dentro del primer millón de candidatos y no
representa una pasada completa.

## Notebook para macOS

El recorrido visual está en
[`notebooks/Fulcrum_DNI_PoC_Mac.ipynb`](notebooks/Fulcrum_DNI_PoC_Mac.ipynb).
Genera figuras en alta resolución sin rutas locales ni elementos de la interfaz
de Jupyter. La instalación y la selección de capturas se explican en la
[`guía de macOS`](notebooks/GUIA_MAC_JUPYTER.md).

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-notebook.txt
jupyter lab notebooks/Fulcrum_DNI_PoC_Mac.ipynb
```

La ejecución principal recorre 100.000.000 de candidatos. Las mediciones de un
solo hilo y de sal global conocida son opcionales y están desactivadas por
defecto.

## Modelo experimental

El generador crea 12 identidades marcadas como `PERSONA_SINTETICA_001`, correos
en el dominio reservado `.invalid` y sustitutos financieros ficticios. Las
tablas representan un esquema empresarial simplificado:

- `staging_identity`: identificador en claro y atributos de alta atribución.
- `customer_core`: `SHA256(NIF)` y clave de enlace estable.
- `contact_details`: contacto y número de póliza sintéticos.
- `financial_profile`: datos financieros sustitutos.
- `case_notes`: identificador con una sustitución reversible débil.
- `auth_users`: contraseñas ficticias protegidas con scrypt.
- `defended_identifiers`: comparativa entre sal por fila, HMAC y tokenización.

El formato canónico que se hashea es el NIF completo:

```text
00000000T
00000001R
...
99999999R
```

La existencia de valores no emitidos reduciría el dominio real; nunca lo
aumentaría. Esta PoC modela el espacio sintáctico y no pretende describir el
registro administrativo de documentos emitidos. Una cadena generada podría
coincidir accidentalmente con un identificador emitido, pero no procede de una
persona ni se relaciona con atributos reales.

## Qué cambia cada defensa

| Diseño | Efecto si se extrae la base de datos |
| --- | --- |
| `SHA256(DNI)` | Una pasada permite comprobar todos los objetivos que compartan normalización y transformación. |
| `SHA256(sal_global ‖ DNI)` con sal conocida | Exige recalcular para esa sal, pero mantiene una sola pasada para todos los objetivos. |
| `SHA256(sal_fila ‖ DNI)` con sal almacenada | Evita amortizar una única pasada masiva; no impide una búsqueda dirigida por registro. |
| `HMAC-SHA256(clave, DNI)` | Sin la clave no se pueden validar candidatos; la clave debe estar separada de los datos extraídos. |
| Token aleatorio y correspondencia separada | No existe una relación matemática que enumerar; la tabla de correspondencia se convierte en el activo crítico. |

Una función lenta como Argon2id eleva el coste, pero suele resultar incómoda
para uniones deterministas. Cuando se necesita vinculación, HMAC con claves de
alta entropía, separación por contexto y custodia en KMS/HSM suele encajar
mejor. Cuando no se necesita, la tokenización aleatoria reduce la
vinculabilidad.

## Interpretación y límites

- La PoC prueba recuperabilidad técnica en un modelo concreto; no determina por
  sí sola el cumplimiento jurídico de una organización.
- Los datos seudonimizados siguen siendo datos personales cuando pueden
  atribuirse con información adicional razonablemente disponible.
- La vinculación entre conjuntos requiere que coincidan normalización,
  transformación, clave o contexto. No se presupone que dos hashes cualesquiera
  sean enlazables.
- Las referencias a FulcrumSec y GRIT se distinguen entre afirmaciones del actor,
  evaluación publicada y resultados independientes de este laboratorio.
- El análisis regulatorio es informativo y requiere revisión jurídica para un
  caso concreto.

La matriz de afirmaciones está en
[`research/claims_matrix.md`](research/claims_matrix.md) y la metodología
completa en [`research/dossier.md`](research/dossier.md).

## Estructura

```text
src/        enumerador C, generador, reconstrucción, benchmark y validación
notebooks/  recorrido visual para Jupyter/macOS
tests/      pruebas unitarias y de integración sobre un dominio corto
results/    resultados base y manifiesto de integridad
research/   artículo, fuentes, dossier y matriz de afirmaciones
```

## Uso responsable, contribuciones y cita

Lee [`ETHICS.md`](ETHICS.md) antes de ejecutar o modificar el laboratorio. Las
contribuciones deben utilizar únicamente datos sintéticos y seguir
[`CONTRIBUTING.md`](CONTRIBUTING.md). Los problemas de seguridad deben
comunicarse mediante el proceso descrito en [`SECURITY.md`](SECURITY.md).

GitHub puede generar una cita desde [`CITATION.cff`](CITATION.cff). El código se
publica bajo licencia [MIT](LICENSE).
