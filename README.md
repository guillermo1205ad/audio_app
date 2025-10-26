# 🎧 Audio App — Plataforma de Revisión de Transcripciones

## 🧩 Descripción general

**Audio App** es parte del ecosistema **Nuestra MemorIA**, diseñada para revisar y versionar transcripciones de audio.  
Permite importar archivos `.mp3` y sus metadatos JSON (`_new_web_ready.json`), visualizar los segmentos, corregirlos y generar versiones sucesivas en `media/versiones/`.

Desarrollada con **Django 5.1**, autenticación mediante **django-allauth** (usuario local y Google OAuth), e integración con **Whisper Large-v3** para transcripción automática.

---

## ⚙️ Estructura del proyecto

```bash
audio_app/
├── .venv/                     # entorno virtual (no se versiona)
├── codes/                     # scripts auxiliares del pipeline
├── media/
│   ├── audios/                # audios y JSON importados
│   └── versiones/             # versiones generadas (JSON/TXT)
├── review/                    # aplicación Django principal
├── review_project/            # configuración global del proyecto
├── static/                    # archivos estáticos (CSS, JS, íconos)
├── templates/                 # plantillas HTML (login, revisión, etc.)
├── manage.py
├── pyproject.toml             # dependencias (formato uv)
├── uv.lock                    # versiones exactas
├── .gitignore
└── .env                       # variables de entorno
```

---

## 🧰 Requisitos

- Python **≥ 3.10**
- [uv](https://docs.astral.sh/uv/) instalado (`pip install uv`)
- PostgreSQL
- GPU con CUDA (opcional, recomendado)
- Puerto libre **8088**

---

## 🧱 Estructura externa sugerida

Se recomienda mantener una organización clara fuera del repositorio para separar el código fuente, los audios originales, los procesados y los recursos del modelo.  
Una estructura funcional típica sería la siguiente:

```bash
/home/gperaltag/mi_entorno/
├── audio_app/            # código del proyecto Django
├── AUDIOS/               # audios originales y JSON de entrada
│   ├── pruebas/          # audios y JSON base (.mp3 + .json)
│   └── _new_web_ready/   # archivos finales procesados listos para importar
├── audios/               # audios gestionados por Django (MEDIA_ROOT)
└── large-v3/             # modelo Whisper descargado desde Hugging Face
```

> Puedes definir estas rutas con variables de entorno:
> ```bash
> export AUDIO_APP_PATH=/ruta/a/audio_app
> export AUDIOS_PATH=/ruta/a/AUDIOS
> export MEDIA_PATH=/ruta/a/audios
> export WHISPER_PATH=/ruta/a/large-v3
> ```
>
> Estas variables son utilizadas por los scripts del pipeline y por Django para ubicar los recursos externos sin depender de rutas fijas.  
> Puedes agregarlas a tu `~/.bashrc` o exportarlas antes de ejecutar los scripts.

---

## 📦 Instalación

### 1️⃣ Clonar el proyecto

```bash
git clone https://github.com/guillermo1205ad/audio_app.git
cd audio_app
```

### 2️⃣ Crear entorno virtual con `uv`

```bash
uv venv .venv
source .venv/bin/activate
uv sync
```

### 3️⃣ Configurar entorno (.env)

Copia el archivo de ejemplo y ajusta tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus valores personalizados.  
Ejemplo:

```bash
DJANGO_SECRET_KEY="clave_secreta"
DB_NAME="plataforma_revision"
DB_USER="audio_user"
DB_PASSWORD="audios_2025"
EMAIL_HOST_USER="tu_correo@gmail.com"
EMAIL_HOST_PASSWORD="clave_app_gmail"
MEDIA_ROOT="/ruta/a/audio_app/media"
```

---

## 🗄️ Base de datos

Por defecto, el proyecto usa **PostgreSQL**, configurado desde `.env`:

```python
DATABASES = {
    'default': {
        'ENGINE':   os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        'NAME':     os.getenv("DB_NAME", "plataforma_revision"),
        'USER':     os.getenv("DB_USER", "audio_user"),
        'PASSWORD': os.getenv("DB_PASSWORD", ""),
        'HOST':     os.getenv("DB_HOST", "localhost"),
        'PORT':     os.getenv("DB_PORT", "5432"),
    }
}
```

> 💡 **Configuración inicial (solo una vez):**
> ```bash
> psql -U postgres
> CREATE DATABASE plataforma_revision;
> CREATE USER "user_name" WITH PASSWORD 'password';
> GRANT ALL PRIVILEGES ON DATABASE plataforma_revision TO "user_name";
> ```

Luego inicializa Django:

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## 🔡 Descargar el modelo Whisper Large-v3

Antes de usar los scripts de transcripción, descarga el modelo desde Hugging Face:

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="openai/whisper-large-v3",
    local_dir="/ruta/a/large-v3",
    local_dir_use_symlinks=False
)
```

Luego define la variable de entorno:

```bash
export WHISPER_PATH=/ruta/a/large-v3
```

---

## 🎬 Pipeline de procesamiento de audio

Primero ejecutar `codes/transcribir.py`. A partir de acá, el flujo completo se ejecuta desde `codes/pipeline_audio.py`, que automatiza:

| Paso | Script | Descripción |
|------|--------|-------------|
| 1️⃣ | `agregar_audio_a_json.py` | Asocia cada `.mp3` con su `.json` |
| 2️⃣ | `metricas_correcciones.py` | Calcula métricas y umbrales de confianza |
| 3️⃣ | `collect_new_web_ready.py` | Copia los JSON finales a `_new_web_ready/` |


Ejemplo:

```bash
python3 codes/transcribir.py
python3 codes/pipeline_audio.py
```

---

## 📦 Importar audios en Django

Importa los audios procesados a la base de datos con:

```bash
python manage.py import_media /ruta/a/AUDIOS/_new_web_ready
```

Esto:
- Copia los MP3 y JSON a `media/audios/`
- Crea registros `Audio`
- Carga los segmentos definidos en los JSON `_new_web_ready.json`

---

## 🧭 Ejecutar la aplicación

Inicia el servidor de desarrollo en el puerto **8088**:

```bash
python manage.py runserver 0.0.0.0:8088
```

Accede en tu navegador:
```
http://127.0.0.1:8088
```

---

## 🔑 Autenticación

- **Usuario local**: usa el creado con `createsuperuser`
- **Google OAuth**: inicia sesión con Google (preconfigurado)

URI de redirección:
```
http://127.0.0.1:8088/accounts/google/login/callback/
```

---

## 🧾 Versionado automático

Cada corrección genera versiones en `media/versiones/`:

```
audio_modificado_YYYYMMDD_HHMMSS.json
audio_final_YYYYMMDD_HHMMSS.txt
```

Permite rastrear la evolución de cada revisión.

## 🧩 Créditos

Proyecto desarrollado por  
**Guillermo Peralta**  
Pontificia Universidad Católica de Chile  
Doctorado en Ciencias de la Computación  
📧 gperaltag@estudiante.uc.cl  

---

> 💡 Si al ejecutar `python manage.py runserver` ves un error de migraciones, ejecuta:
> ```bash
> python manage.py makemigrations
> python manage.py migrate
> ```

## 🗓️ Última actualización
**26 de octubre de 2025**
