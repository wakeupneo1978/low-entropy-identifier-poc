# Guía de ejecución en Mac y Jupyter

Esta guía ejecuta la PoC **exclusivamente con datos sintéticos** y genera
figuras preparadas para acompañar el artículo «Cien millones no son entropía».

## 1. Preparar el Mac

Abre Terminal y comprueba que tienes las herramientas de compilación:

```bash
xcode-select -p
```

Si el comando falla:

```bash
xcode-select --install
```

Comprueba Homebrew:

```bash
brew --version
```

Si no está instalado, utiliza las instrucciones oficiales de
<https://brew.sh/>. Después instala OpenSSL 3 y `pkg-config`:

```bash
brew install openssl@3 pkg-config
```

## 2. Crear un entorno de Python aislado

Desde la carpeta clonada del proyecto:

```bash
cd ~/Projects/low-entropy-identifier-poc
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-notebook.txt
```

El proyecto requiere Python 3.11 o posterior. Si `python3` es anterior, instala
una versión reciente con Homebrew y vuelve a crear el entorno:

```bash
brew install python@3.12
```

## 3. Abrir el notebook

Con el entorno `.venv` activado y desde la raíz del proyecto:

```bash
jupyter lab notebooks/Fulcrum_DNI_PoC_Mac.ipynb
```

En Jupyter selecciona el kernel de `.venv` si no aparece automáticamente.

Ejecuta las celdas en orden. La primera parte comprueba dependencias, compila el
enumerador y ejecuta las pruebas. Después se inicia el recorrido completo de
100.000.000 de candidatos.

## 4. Recorrido recomendado

El notebook contiene tres mediciones:

1. Reconstrucción completa con todos los hilos lógicos detectados.
2. Reconstrucción opcional con un único hilo.
3. Comparación opcional entre SHA-256 sin sal y una sal global conocida.

La primera es suficiente para demostrar la tesis central. Las otras dos son
opcionales porque cada una añade otra pasada completa. Pueden tardar desde
decenas de segundos hasta varios minutos, según el Mac, la temperatura y la
versión de OpenSSL.

Para activar las dos mediciones adicionales, cambia en la primera celda:

```python
RUN_SINGLE_THREAD = True
RUN_KNOWN_SALT_BENCHMARK = True
```

No utilices otras aplicaciones intensivas mientras haces las mediciones. Para
una cifra publicable, reinicia el kernel y repite cada benchmark al menos cinco
veces; publica mediana, mínimo y máximo, no solo la mejor ejecución.

## 5. Capturas recomendadas

El notebook guarda figuras PNG de alta resolución en
`results/figures_mac/`. Las tres capturas principales son:

1. `01_dominio_vs_hash.png`: acompaña «La pregunta incómoda: 26,6 bits».
2. `03_resultado_reconstruccion.png`: acompaña los resultados experimentales.
3. `04_tres_caminos.png`: acompaña «No hay una debilidad, hay tres».

Capturas opcionales:

- `02_modelo_datos.png`: explica la clave de enlace entre tablas.
- `05_perfiles_sinteticos.png`: muestra el resultado de los joins; debe
  conservar siempre la etiqueta visible «DATOS SINTÉTICOS».
- `06_salt_global_conocida.png`: demuestra que una sal global conocida no
  elimina la enumeración.
- `07_matriz_controles.png`: acompaña la sección de soluciones.
- `08_multihilo_vs_1hilo.png`: documenta el efecto de fijar un hilo.

En macOS puedes capturar una región con `Mayús + Comando + 4`. Para el artículo
es preferible insertar directamente los PNG generados: tienen mayor resolución,
no muestran el nombre de usuario, rutas locales, pestañas ni elementos de
Jupyter.

## 6. Resultados y trazabilidad

La ejecución crea:

- `results/reconstruction_mac_multithread.json`
- `results/reconstruction_mac_1thread.json`, si se activa
- `results/benchmark_mac.json`, si se activa
- `results/mac_environment.json`
- `results/mac_run_manifest.sha256`
- `results/figures_mac/*.png`

Conserva esos ficheros junto con la versión publicada del código. Son la
evidencia que permite relacionar las cifras del artículo con hardware, número
de hilos, entorno y código concretos.

## 7. Problemas frecuentes

### `openssl/sha.h file not found`

En Terminal:

```bash
export PKG_CONFIG_PATH="$(brew --prefix openssl@3)/lib/pkgconfig"
pkg-config --cflags --libs openssl
make
```

Después reinicia el kernel y vuelve a ejecutar la celda de compilación.

### El notebook usa otro Python

Comprueba la ruta del kernel en la primera celda. Activa `.venv`, instala un
kernel explícito y reinicia Jupyter:

```bash
python -m pip install ipykernel
python -m ipykernel install --user --name fulcrum-dni-poc \
  --display-name "Fulcrum DNI PoC"
```

### El Mac se calienta o cambia mucho el tiempo

Es normal que macOS modifique frecuencia y planificación térmica. Deja enfriar
el equipo, cierra cargas intensivas y realiza varias repeticiones. No selecciones
la ejecución más rápida; utiliza una estadística agregada.

## 8. Límite ético

No sustituyas los hashes sintéticos por identificadores de filtraciones,
clientes o terceros. La finalidad del laboratorio es medir una propiedad
criptográfica con un dominio sintáctico público, no procesar datos personales.
