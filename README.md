# 🤖 RAG con Telegram y Ollama

Bot de Telegram que responde preguntas sobre documentos PDF usando **RAG** (*Retrieval-Augmented Generation*) con una **IA que corre 100% local** gracias a [Ollama](https://ollama.com).

Le hacés una pregunta al bot, busca los fragmentos más relevantes de tus PDFs y genera una respuesta basada **solo** en esa información, indicando de qué archivo y página la sacó.

## ✨ Características

- 📄 Carga y procesa documentos PDF.
- 🔍 Búsqueda semántica con una base de datos vectorial ([ChromaDB](https://www.trychroma.com)).
- 🧠 Respuestas generadas por un modelo de lenguaje local, sin APIs pagas y sin enviar tus documentos a internet.
- 📌 Cada respuesta incluye las fuentes (archivo y página).
- 🚫 Si la información no está en los documentos, lo indica en lugar de inventar.
- 💬 Interfaz a través de Telegram.

## 🛠️ Tecnologías

| Herramienta | Uso |
|---|---|
| **Python** | Lenguaje del proyecto |
| **Ollama** | Ejecución local de los modelos de IA |
| **qwen3.5:4b** | Modelo que genera las respuestas |
| **qwen3-embedding:0.6b** | Modelo que convierte texto en vectores |
| **ChromaDB** | Base de datos vectorial |
| **python-telegram-bot** | Conexión con Telegram |
| **pypdf** | Lectura de PDFs |
| **python-dotenv** | Manejo de variables de entorno |

## ⚙️ Cómo funciona

```
PDFs ──► ingest.py ──► fragmentos + embeddings ──► ChromaDB
                                                      │
Usuario ──► Telegram ──► bot.py ──► rag.py ──► busca fragmentos relevantes
                                       │
                                       └──► Ollama genera la respuesta ──► Telegram
```

1. **Carga (`ingest.py`)**: lee los PDFs, los divide en fragmentos y guarda sus embeddings en ChromaDB.
2. **Búsqueda (`rag.py`)**: convierte la pregunta en un vector y recupera los fragmentos más parecidos.
3. **Generación (`rag.py`)**: le pasa esos fragmentos al modelo, que responde usando solo esa información.
4. **Bot (`bot.py`)**: recibe las preguntas por Telegram y devuelve la respuesta con sus fuentes.

## 📁 Estructura del proyecto

```
rag-telegram/
├── docs/              # PDFs que el bot va a usar como conocimiento
├── chroma_db/         # Base vectorial (se genera sola, no se sube a git)
├── config.py          # Configuración general
├── ingest.py          # Carga los PDFs en ChromaDB
├── rag.py             # Lógica de búsqueda y generación de respuestas
├── bot.py             # Bot de Telegram
├── test_ollama.py     # Prueba rápida de conexión con Ollama
├── requirements.txt   # Dependencias
├── .env.example       # Ejemplo de variables de entorno
└── .gitignore
```

## 📋 Requisitos

- Python 3.10 o superior
- [Ollama](https://ollama.com/download) instalado y en ejecución
- Una cuenta de Telegram
- Recomendado: 8 GB de RAM o más

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Niquit0u/rag-telegram.git
cd rag-telegram
```

### 2. Crear y activar el entorno virtual

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 4. Descargar los modelos de Ollama

```bash
ollama pull qwen3.5:4b
ollama pull qwen3-embedding:0.6b
```

### 5. Crear el bot de Telegram

1. En Telegram, abrí un chat con [@BotFather](https://t.me/BotFather).
2. Enviá `/newbot` y seguí los pasos (nombre y usuario terminado en `bot`).
3. Copiá el **token** que te entrega.

### 6. Configurar las variables de entorno

Copiá el archivo de ejemplo y completalo:

```bash
cp .env.example .env
```

```env
TELEGRAM_TOKEN=tu_token_aca
LLM_MODEL=qwen3.5:4b
EMBED_MODEL=qwen3-embedding:0.6b
```

> ⚠️ Nunca subas el archivo `.env` al repositorio: contiene el token de tu bot.

## ▶️ Uso

### 1. Agregar documentos

Copiá tus archivos PDF en la carpeta `docs/`.

### 2. Cargar los documentos en la base

```bash
python ingest.py
```

> Volvé a ejecutarlo cada vez que agregues, modifiques o elimines PDFs.

### 3. (Opcional) Probar desde la consola

```bash
python rag.py
```

### 4. Iniciar el bot

```bash
python bot.py
```

Buscá tu bot en Telegram, enviá `/start` y empezá a hacer preguntas.

### Comandos del bot

| Comando | Descripción |
|---|---|
| `/start` | Mensaje de bienvenida |
| `/ayuda` | Explica cómo usar el bot |

## 🔧 Configuración

Los parámetros principales se ajustan en `config.py`:

| Parámetro | Valor | Descripción |
|---|---|---|
| `TAMANO_FRAGMENTO` | 800 | Tamaño de cada fragmento (en caracteres) |
| `SOLAPAMIENTO` | 150 | Caracteres compartidos entre fragmentos consecutivos |
| `FRAGMENTOS_POR_CONSULTA` | 4 | Fragmentos que se le pasan al modelo por pregunta |

Los modelos se pueden cambiar desde el `.env`.

> ⚠️ Si cambiás `EMBED_MODEL`, tenés que volver a ejecutar `ingest.py`, porque los vectores guardados dependen del modelo con el que se generaron.

## 📝 Notas

- El bot solo responde mientras `bot.py` esté en ejecución y Ollama esté activo.
- Los PDFs escaneados (imágenes) no tienen texto extraíble; necesitan pasar antes por un OCR.
- Las respuestas dependen de la calidad de los documentos cargados.

## 👤 Autor

**Arias Navarrete Nicolás**

[GitHub](https://github.com/Niquit0u)
