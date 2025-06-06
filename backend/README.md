# DXF Analyzer API

API para análisis y visualización de archivos DXF, desarrollada con FastAPI.

## Características

- Análisis de archivos DXF
- Detección de entidades fantasma
- Cálculo de longitudes de corte
- Generación de bounding box
- Estadísticas detalladas del diseño

## Requisitos

- Python 3.11+
- FastAPI
- ezdxf
- uvicorn

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/Arkcutt12/Backend_dxf.git
cd Backend_dxf
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Iniciar el servidor:
```bash
uvicorn main:app --reload
```

2. Acceder a la documentación:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

- `POST /analyze-dxf`: Analiza un archivo DXF
- `GET /health`: Health check
- `GET /`: Información de la API

## Docker

Para ejecutar con Docker:

```bash
docker build -t dxf-analyzer .
docker run -p 8000:8000 dxf-analyzer
```

## Railway

El proyecto está configurado para desplegarse en Railway. El archivo `railway.json` contiene la configuración necesaria.

## Licencia

MIT 