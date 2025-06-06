from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import ezdxf
import tempfile
import os
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import uvicorn
from pydantic import BaseModel

# Modelos de datos
@dataclass
class Point:
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def to_dict(self):
        return {"x": self.x, "y": self.y}

@dataclass
class BoundingBox:
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    
    @property
    def width(self) -> float:
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        return self.max_y - self.min_y
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    def to_dict(self):
        return {
            "min_x": self.min_x,
            "min_y": self.min_y,
            "max_x": self.max_x,
            "max_y": self.max_y,
            "width": self.width,
            "height": self.height,
            "area": self.area
        }

class EntityType(Enum):
    LINE = "LINE"
    LWPOLYLINE = "LWPOLYLINE"
    POLYLINE = "POLYLINE"
    CIRCLE = "CIRCLE"
    ARC = "ARC"
    SPLINE = "SPLINE"

@dataclass
class ProcessedEntity:
    entity_type: str
    points: List[Dict[str, float]]
    length: float
    layer: str
    is_valid: bool
    rejection_reason: Optional[str] = None
    
    def to_dict(self):
        return {
            "entity_type": self.entity_type,
            "points": self.points,
            "length": self.length,
            "layer": self.layer,
            "is_valid": self.is_valid,
            "rejection_reason": self.rejection_reason
        }

# Modelos Pydantic para validación
class AnalysisResponse(BaseModel):
    success: bool
    statistics: Dict
    bounding_box: Dict
    cut_length: Dict
    entities: Dict
    error: Optional[str] = None

# Procesador DXF mejorado
class DXFProcessor:
    def __init__(self):
        self.valid_entities: List[ProcessedEntity] = []
        self.phantom_entities: List[ProcessedEntity] = []
        
    def get_entity_points(self, entity) -> List[Point]:
        """Extrae puntos de diferentes tipos de entidades"""
        points = []
        
        try:
            if entity.dxftype() == "LINE":
                points = [
                    Point(float(entity.dxf.start.x), float(entity.dxf.start.y)),
                    Point(float(entity.dxf.end.x), float(entity.dxf.end.y))
                ]
            elif entity.dxftype() == "LWPOLYLINE":
                for point in entity.get_points():
                    points.append(Point(float(point[0]), float(point[1])))
            elif entity.dxftype() == "POLYLINE":
                for vertex in entity.vertices:
                    points.append(Point(float(vertex.dxf.location.x), float(vertex.dxf.location.y)))
            elif entity.dxftype() == "CIRCLE":
                center = Point(float(entity.dxf.center.x), float(entity.dxf.center.y))
                radius = float(entity.dxf.radius)
                # 16 puntos para representar el círculo
                for i in range(16):
                    angle = 2 * math.pi * i / 16
                    x = center.x + radius * math.cos(angle)
                    y = center.y + radius * math.sin(angle)
                    points.append(Point(x, y))
            elif entity.dxftype() == "ARC":
                center = Point(float(entity.dxf.center.x), float(entity.dxf.center.y))
                radius = float(entity.dxf.radius)
                start_angle = math.radians(float(entity.dxf.start_angle))
                end_angle = math.radians(float(entity.dxf.end_angle))
                segments = 16
                for i in range(segments + 1):
                    angle = start_angle + (end_angle - start_angle) * i / segments
                    x = center.x + radius * math.cos(angle)
                    y = center.y + radius * math.sin(angle)
                    points.append(Point(x, y))
        except Exception as e:
            print(f"Error extracting points from {entity.dxftype()}: {e}")
        
        return points
    
    def calculate_entity_length(self, entity, points: List[Point]) -> float:
        """Calcula la longitud de la entidad"""
        try:
            if entity.dxftype() == "LINE":
                return points[0].distance_to(points[1]) if len(points) >= 2 else 0
            elif entity.dxftype() in ["LWPOLYLINE", "POLYLINE"]:
                total_length = 0
                for i in range(len(points) - 1):
                    total_length += points[i].distance_to(points[i + 1])
                return total_length
            elif entity.dxftype() == "CIRCLE":
                return 2 * math.pi * float(entity.dxf.radius)
            elif entity.dxftype() == "ARC":
                radius = float(entity.dxf.radius)
                start_angle = math.radians(float(entity.dxf.start_angle))
                end_angle = math.radians(float(entity.dxf.end_angle))
                return abs(end_angle - start_angle) * radius
        except Exception as e:
            print(f"Error calculating length: {e}")
        return 0
    
    def is_phantom_entity(self, entity, points: List[Point], design_center: Point, max_design_dimension: float) -> Tuple[bool, str]:
        """Detecta entidades fantasma"""
        if not points:
            return True, "Sin puntos válidos"
        
        try:
            # 1. Filtrar por capa
            layer_name = str(entity.dxf.layer).upper()
            phantom_layers = {'DEFPOINTS', 'PHANTOM', 'HIDDEN', 'CONSTRUCTION', 'TEMP'}
            if layer_name in phantom_layers:
                return True, f"Capa fantasma: {layer_name}"
            
            # 2. Filtrar entidades invisibles
            if hasattr(entity.dxf, 'invisible') and entity.dxf.invisible:
                return True, "Entidad invisible"
            
            # 3. Filtros específicos para líneas
            if entity.dxftype() == "LINE" and len(points) >= 2:
                start, end = points[0], points[1]
                
                # Líneas que van al origen
                if (abs(start.x) < 0.001 and abs(start.y) < 0.001) or \
                   (abs(end.x) < 0.001 and abs(end.y) < 0.001):
                    return True, "Línea conecta con origen (0,0)"
                
                # Líneas extremadamente largas
                line_length = start.distance_to(end)
                if line_length > max_design_dimension * 10:
                    return True, f"Línea demasiado larga: {line_length:.2f}mm"
                
                # Líneas muy alejadas del centro del diseño
                line_center = Point((start.x + end.x) / 2, (start.y + end.y) / 2)
                distance_to_design = line_center.distance_to(design_center)
                if distance_to_design > max_design_dimension * 5:
                    return True, f"Línea alejada del diseño: {distance_to_design:.2f}mm"
            
            # 4. Coordenadas extremas
            for point in points:
                if abs(point.x) > 50000 or abs(point.y) > 50000:
                    return True, f"Coordenadas extremas: ({point.x:.2f}, {point.y:.2f})"
            
        except Exception as e:
            return True, f"Error procesando entidad: {str(e)}"
        
        return False, "Entidad válida"
    
    def get_design_statistics(self, entities: List) -> Tuple[Point, float]:
        """Calcula estadísticas del diseño"""
        all_points = []
        
        for entity in entities:
            if entity.dxftype() in ["LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC"]:
                points = self.get_entity_points(entity)
                all_points.extend(points)
        
        if not all_points:
            return Point(0, 0), 1000
        
        # Centro de masa
        center_x = sum(p.x for p in all_points) / len(all_points)
        center_y = sum(p.y for p in all_points) / len(all_points)
        center = Point(center_x, center_y)
        
        # Dimensión máxima
        min_x = min(p.x for p in all_points)
        max_x = max(p.x for p in all_points)
        min_y = min(p.y for p in all_points)
        max_y = max(p.y for p in all_points)
        
        max_dimension = max(max_x - min_x, max_y - min_y)
        
        return center, max_dimension
    
    def process_dxf_file(self, file_path: str) -> Dict:
        """Procesa el archivo DXF y devuelve datos JSON"""
        try:
            # Cargar archivo DXF
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()
            all_entities = list(msp)
            
            # Reset de listas
            self.valid_entities = []
            self.phantom_entities = []
            
            print(f"Procesando {len(all_entities)} entidades...")
            
            # Calcular estadísticas del diseño
            design_center, max_design_dimension = self.get_design_statistics(all_entities)
            
            # Procesar cada entidad
            for entity in all_entities:
                if entity.dxftype() not in ["LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC"]:
                    continue
                
                points = self.get_entity_points(entity)
                if not points:
                    continue
                
                # Verificar si es fantasma
                is_phantom, reason = self.is_phantom_entity(entity, points, design_center, max_design_dimension)
                
                # Crear entidad procesada
                processed_entity = ProcessedEntity(
                    entity_type=entity.dxftype(),
                    points=[p.to_dict() for p in points],
                    length=self.calculate_entity_length(entity, points),
                    layer=str(entity.dxf.layer),
                    is_valid=not is_phantom,
                    rejection_reason=reason if is_phantom else None
                )
                
                if is_phantom:
                    self.phantom_entities.append(processed_entity)
                else:
                    self.valid_entities.append(processed_entity)
            
            # Calcular bounding box y métricas
            bbox = self.calculate_bounding_box(self.valid_entities)
            total_cut_length = sum(entity.length for entity in self.valid_entities)
            
            print(f"Procesamiento completado: {len(self.valid_entities)} válidas, {len(self.phantom_entities)} fantasma")
            
            # Generar respuesta
            result = {
                "success": True,
                "statistics": {
                    "total_entities": len(all_entities),
                    "valid_entities": len(self.valid_entities),
                    "phantom_entities": len(self.phantom_entities),
                    "design_center": design_center.to_dict(),
                    "max_design_dimension": max_design_dimension
                },
                "bounding_box": bbox.to_dict(),
                "cut_length": {
                    "total_mm": round(total_cut_length, 2),
                    "total_m": round(total_cut_length / 1000, 3)
                },
                "entities": {
                    "valid": [entity.to_dict() for entity in self.valid_entities],
                    "phantom": [entity.to_dict() for entity in self.phantom_entities]
                }
            }
            
            return result
            
        except Exception as e:
            print(f"Error procesando DXF: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error procesando archivo DXF"
            }
    
    def calculate_bounding_box(self, entities: List[ProcessedEntity]) -> BoundingBox:
        """Calcula bounding box de entidades válidas"""
        if not entities:
            return BoundingBox(0, 0, 0, 0)
        
        all_points = []
        for entity in entities:
            for point_dict in entity.points:
                all_points.append(Point(point_dict["x"], point_dict["y"]))
        
        if not all_points:
            return BoundingBox(0, 0, 0, 0)
        
        min_x = min(p.x for p in all_points)
        max_x = max(p.x for p in all_points)
        min_y = min(p.y for p in all_points)
        max_y = max(p.y for p in all_points)
        
        return BoundingBox(min_x, min_y, max_x, max_y)

# Inicializar FastAPI
app = FastAPI(
    title="DXF Analyzer API",
    description="API para análisis y visualización de archivos DXF",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, usar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia del procesador
processor = DXFProcessor()

@app.post("/analyze-dxf", response_model=None)
async def analyze_dxf(file: UploadFile = File(...)):
    """
    Analiza un archivo DXF y devuelve información detallada
    """
    # Validar tipo de archivo
    if not file.filename or not file.filename.lower().endswith('.dxf'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un DXF válido")
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp_file:
        try:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error leyendo archivo: {str(e)}")
    
    try:
        # Procesar archivo
        result = processor.process_dxf_file(tmp_file_path)
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando DXF: {str(e)}")
    
    finally:
        # Limpiar archivo temporal
        try:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        except Exception:
            pass

@app.get("/")
async def root():
    """Información de la API"""
    return {
        "name": "DXF Analyzer API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "analyze": "POST /analyze-dxf",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "DXF Analyzer API"}

if __name__ == "__main__":
    print("🚀 Iniciando DXF Analyzer API...")
    print("📊 Endpoints disponibles:")
    print("   • POST /analyze-dxf - Analizar archivo DXF")
    print("   • GET /health - Health check")
    print("   • GET / - Info de la API")
    print("   • GET /docs - Documentación Swagger")
    print("\n🌐 Servidor ejecutándose en: http://localhost:8000")
    
    uvicorn.run(
        "main:app",  # Cambiar por el nombre de tu archivo si es diferente
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 