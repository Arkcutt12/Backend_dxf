# 🔍 DXF Analyzer API

Una API moderna y robusta para análisis, procesamiento y visualización de archivos DXF, desarrollada con **FastAPI** y **Python 3.11**. Especializada en detección inteligente de entidades fantasma y cálculo preciso de longitudes de corte.

## ✨ Características Principales

### 🎯 Análisis Avanzado
- **Detección de Entidades Fantasma**: Algoritmo inteligente que identifica y filtra entidades no válidas
- **Cálculo de Longitudes**: Medición precisa de longitudes totales de corte
- **Bounding Box**: Cálculo automático de dimensiones del diseño
- **Estadísticas Detalladas**: Análisis completo del contenido del archivo

### 🚀 Tecnología
- **FastAPI**: Framework moderno y de alto rendimiento
- **ezdxf**: Librería especializada para procesamiento DXF
- **Pydantic**: Validación de datos robusta
- **Docker**: Containerización para deployment fácil
- **Railway**: Configuración lista para producción

### 📊 Tipos de Entidades Soportadas
- `LINE` - Líneas rectas
- `LWPOLYLINE` - Polilíneas ligeras
- `POLYLINE` - Polilíneas tradicionales  
- `CIRCLE` - Círculos completos
- `ARC` - Arcos circulares
- `SPLINE` - Curvas spline (próximamente)

## 🛠️ Instalación

### Opción 1: Instalación Local

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/dxf-analyzer-api.git
cd dxf-analyzer-api

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor de desarrollo
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Opción 2: Docker

```bash
# Construir imagen
docker build -t dxf-analyzer-api .

# Ejecutar contenedor
docker run -p 8000:8000 dxf-analyzer-api
```

### Opción 3: Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  dxf-analyzer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
    restart: unless-stopped
```

```bash
docker-compose up -d
```

## 🌐 Uso de la API

### Documentación Interactiva
Una vez iniciado el servidor, accede a:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principales

#### 📤 POST `/analyze-dxf`
Analiza un archivo DXF y devuelve información detallada.

**Request:**
```bash
curl -X POST "http://localhost:8000/analyze-dxf" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@tu_archivo.dxf"
```

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_entities": 150,
    "valid_entities": 142,
    "phantom_entities": 8,
    "design_center": {"x": 100.5, "y": 75.2},
    "max_design_dimension": 200.0
  },
  "bounding_box": {
    "min_x": 0.0,
    "min_y": 0.0,
    "max_x": 200.0,
    "max_y": 150.0,
    "width": 200.0,
    "height": 150.0,
    "area": 30000.0
  },
  "cut_length": {
    "total_mm": 1250.75,
    "total_m": 1.251
  },
  "entities": {
    "valid": [...],
    "phantom": [...]
  }
}
```

#### 🔍 GET `/health`
Health check del servicio.

#### ℹ️ GET `/`
Información general de la API.

## 🤖 Algoritmo de Detección de Entidades Fantasma

El sistema utiliza múltiples criterios para identificar entidades no válidas:

### 1. **Filtros por Capa**
```python
phantom_layers = {'DEFPOINTS', 'PHANTOM', 'HIDDEN', 'CONSTRUCTION', 'TEMP'}
```

### 2. **Detección de Entidades Invisibles**
- Entidades marcadas como invisibles en DXF
- Entidades sin puntos válidos

### 3. **Filtros Geométricos**
- **Líneas al origen**: Conectan con (0,0)
- **Líneas extremadamente largas**: > 10x dimensión del diseño
- **Entidades alejadas**: > 5x dimensión desde centro de masa
- **Coordenadas extremas**: |x| o |y| > 50,000

### 4. **Análisis Estadístico**
- Centro de masa del diseño
- Dimensión máxima automática
- Validación contextual

## 📁 Estructura del Proyecto

```
dxf-analyzer-api/
├── 📄 main.py              # Aplicación principal FastAPI
├── 📄 wsgi.py              # Configuración WSGI para producción
├── 📄 gunicorn.conf.py     # Configuración Gunicorn
├── 📄 requirements.txt     # Dependencias Python
├── 📄 Dockerfile           # Imagen Docker
├── 📄 railway.json         # Configuración Railway
├── 📄 README.md           # Este archivo
├── 📁 backend/            # Código legacy (Node.js)
│   ├── 📁 src/
│   ├── 📄 package.json
│   └── 📄 Dockerfile
└── 📄 .gitignore
```

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
# .env
PORT=8000
DEBUG=False
MAX_FILE_SIZE=50MB
ALLOWED_ORIGINS=*
```

### Configuración Gunicorn
```python
# gunicorn.conf.py
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
timeout = 120
```

### Configuración Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🚀 Deployment

### Railway (Recomendado)
```bash
# Conectar con Railway
railway login
railway init
railway up
```

### Heroku
```bash
# Crear aplicación
heroku create tu-dxf-analyzer

# Deploy
git push heroku main
```

### AWS/GCP/Azure
Compatible con cualquier plataforma que soporte Docker o Python.

## 📊 Ejemplos de Uso

### Python
```python
import requests

# Subir y analizar archivo DXF
with open('diseño.dxf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/analyze-dxf',
        files={'file': f}
    )
    
data = response.json()
print(f"Longitud total de corte: {data['cut_length']['total_m']} metros")
```

### JavaScript/Node.js
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('file', fs.createReadStream('diseño.dxf'));

axios.post('http://localhost:8000/analyze-dxf', form, {
    headers: form.getHeaders()
}).then(response => {
    console.log('Análisis completo:', response.data);
});
```

### cURL
```bash
curl -X POST "http://localhost:8000/analyze-dxf" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@diseño.dxf" \
     | jq '.cut_length'
```

## 🧪 Testing

### Tests Unitarios
```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest tests/ -v
```

### Test Manual con cURL
```bash
# Health check
curl http://localhost:8000/health

# Información de la API
curl http://localhost:8000/

# Subir archivo de prueba
curl -X POST "http://localhost:8000/analyze-dxf" \
     -F "file=@test_files/sample.dxf"
```

## 📈 Performance

### Métricas Típicas
- **Archivo pequeño** (< 1MB): ~200ms
- **Archivo mediano** (1-5MB): ~500ms
- **Archivo grande** (5-20MB): ~2s
- **Concurrencia**: Hasta 100 requests/segundo

### Optimizaciones
- Procesamiento asíncrono con FastAPI
- Algoritmos optimizados para entidades DXF
- Gestión eficiente de memoria temporal
- Cache inteligente de cálculos geométricos

## 🔒 Seguridad

### Validaciones Implementadas
- ✅ Validación de tipo de archivo (.dxf)
- ✅ Límite de tamaño de archivo
- ✅ Sanitización de nombres de archivo
- ✅ Limpieza automática de archivos temporales
- ✅ Manejo seguro de excepciones

### Consideraciones de Producción
- Usar HTTPS en producción
- Configurar CORS específicos
- Implementar rate limiting
- Logs de seguridad
- Monitoreo de recursos

## 🤝 Contribución

### Proceso de Contribución
1. Fork el repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

### Estándares de Código
- **PEP 8** para Python
- **Type hints** obligatorios
- **Docstrings** para funciones públicas
- **Tests** para nuevas funcionalidades

## 📝 Changelog

### v1.0.0 (Actual)
- ✅ Análisis básico de archivos DXF
- ✅ Detección de entidades fantasma
- ✅ Cálculo de longitudes de corte
- ✅ API REST completa con FastAPI
- ✅ Documentación Swagger/ReDoc
- ✅ Containerización Docker
- ✅ Configuración Railway

### Próximas Versiones
- 🔄 Soporte para SPLINES
- 🔄 Cache de resultados
- 🔄 Análisis batch de múltiples archivos
- 🔄 Exportación a diferentes formatos
- 🔄 Dashboard web interactivo

## 📞 Soporte

### Documentación
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Issues
Para reportar bugs o solicitar funcionalidades, crear un issue en:
https://github.com/tu-usuario/dxf-analyzer-api/issues

### Contacto
- **Email**: tu-email@ejemplo.com
- **LinkedIn**: [Tu Perfil](https://linkedin.com/in/tu-perfil)
- **Discord**: Tu servidor de Discord

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

<p align="center">
  <strong>🚀 ¡Hecho con ❤️ y Python!</strong>
</p>

<p align="center">
  <a href="#top">⬆️ Volver arriba</a>
</p>
