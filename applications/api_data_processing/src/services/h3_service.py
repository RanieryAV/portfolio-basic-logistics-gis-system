import json
import os
import logging
import h3
from shapely.geometry import shape
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text, func
from domain.config.database_config import SessionLocal, engine, Base
from domain.repositories.data_processing.postal_agencies import PostalAgencies
from domain.repositories.data_processing.neighborhoods import Neighborhoods
from domain.repositories.data_processing.alagoas_streets import AlagoasStreets

logger = logging.getLogger(__name__)

def _build_hexagon_feature(h3_index: str, properties: dict) -> dict:
    """
    Utilitário interno para converter um índice H3 em um Polígono GeoJSON nativo (dicionário).
    """
    boundary = h3.cell_to_boundary(h3_index)
    
    # GeoJSON exige ordem (longitude, latitude) e que o anel seja fechado
    geojson_coords = [[(lng, lat) for lat, lng in boundary]]
    geojson_coords[0].append(geojson_coords[0][0]) 
    
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": geojson_coords
        },
        "properties": {"h3_index": h3_index, **properties}
    }


class QueryH3PostalAgenciesService:
    """
    Serviço responsável por buscar as agências postais no PostGIS 
    e convertê-las em uma malha hexagonal H3 (Pontos).
    """
    def __init__(self):
        self.db = SessionLocal()

    def execute(self, resolution: int = 8):
        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS logistics_gis"))
            self.db.commit()
            Base.metadata.create_all(bind=engine)

            # Utiliza ST_X e ST_Y como o QueryPostalAgenciesService
            agencies_data = self.db.query(
                PostalAgencies,
                func.ST_X(PostalAgencies.location).label("longitude"),
                func.ST_Y(PostalAgencies.location).label("latitude")
            ).all()

            unique_hexagons = {}
            for agency, longitude, latitude in agencies_data:
                try:
                    # latlng_to_cell processa as coordenadas isoladas do ponto
                    h3_index = h3.latlng_to_cell(latitude, longitude, resolution)
                    
                    if h3_index not in unique_hexagons:
                        agency_dict = agency.to_dict()
                        unique_hexagons[h3_index] = _build_hexagon_feature(h3_index, {
                            "name": agency_dict.get("name"),
                            "city": agency_dict.get("city"),
                            "type": "point_agency"
                        })
                except Exception as e:
                    logger.error(f"Falha ao gerar H3 para agência {agency.name}: {str(e)}")
                    continue
                    
            return {"type": "FeatureCollection", "features": list(unique_hexagons.values())}

        except Exception as e:
            logger.error(f"Erro ao consultar agências H3: {str(e)}")
            return {"type": "FeatureCollection", "features": []}
        finally:
            self.db.close()


class QueryH3NeighborhoodsService:
    """
    Serviço responsável por buscar os limites dos bairros no PostGIS 
    e preenchê-los com uma malha hexagonal H3 (Polígonos).
    """
    def __init__(self):
        self.db = SessionLocal()

    def execute(self, resolution: int = 8):
        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS logistics_gis"))
            self.db.commit()
            Base.metadata.create_all(bind=engine)

            # Transforma a geometria diretamente em texto GeoJSON no banco
            neighborhoods_data = self.db.query(
                Neighborhoods,
                func.ST_AsGeoJSON(Neighborhoods.geom).label("geojson_geom"),
                func.ST_X(func.ST_Centroid(Neighborhoods.geom)).label("centroid_lng"),
                func.ST_Y(func.ST_Centroid(Neighborhoods.geom)).label("centroid_lat")
            ).all()

            unique_hexagons = {}
            for area, geojson_str, centroid_lng, centroid_lat in neighborhoods_data:
                try:
                    if not geojson_str:
                        continue

                    geom_dict = json.loads(geojson_str)
                    coords = geom_dict.get("coordinates", [])
                    
                    outer_boundary = []
                    # H3 exige a ordem (latitude, longitude) para o seu polígono interno
                    if geom_dict["type"] == "Polygon":
                        outer_boundary = [(lat, lng) for lng, lat in coords[0]]
                    elif geom_dict["type"] == "MultiPolygon":
                        outer_boundary = [(lat, lng) for lng, lat in coords[0][0]]
                    
                    if not outer_boundary:
                        continue

                    h3_poly = h3.Polygon(outer_boundary)
                    h3_indices = h3.polygon_to_cells(h3_poly, resolution)

                    if len(h3_indices) == 0 and centroid_lat and centroid_lng:
                        fallback_index = h3.latlng_to_cell(centroid_lat, centroid_lng, resolution)
                        h3_indices = {fallback_index}

                    for h3_index in h3_indices:
                        if h3_index not in unique_hexagons:
                            unique_hexagons[h3_index] = _build_hexagon_feature(h3_index, {
                                "code": area.code,
                                "name": area.name,
                                "type": "polygon_area"
                            })
                except Exception as e:
                    logger.error(f"Falha ao processar polígono {area.code}: {str(e)}")
                    continue

            return {"type": "FeatureCollection", "features": list(unique_hexagons.values())}

        except Exception as e:
            logger.error(f"Erro ao consultar bairros H3: {str(e)}")
            return {"type": "FeatureCollection", "features": []}
        finally:
            self.db.close()


class QueryH3AlagoasStreetsService:
    """
    Serviço responsável por buscar a malha de arruamento, expandi-la 
    via ST_Buffer no banco e aplicar os hexágonos H3 (Linhas).
    """
    def __init__(self):
        self.db = SessionLocal()

    def execute(self, resolution: int = 8, buffer_degrees: float = None):
        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS logistics_gis"))
            self.db.commit()
            Base.metadata.create_all(bind=engine)

            # ST_Buffer transforma a LineString em Polygon em tempo de execução
            streets_data = self.db.query(
                AlagoasStreets,
                func.ST_AsGeoJSON(AlagoasStreets.geom).label("geojson_geom")
            ).all()

            unique_hexagons = {}
            for street, geojson_str in streets_data:
                try:
                    if not geojson_str:
                        continue
                    
                    geom_dict = json.loads(geojson_str)
                    coords = geom_dict.get("coordinates", [])
                    
                    lines = []
                    if geom_dict["type"] == "LineString":
                        lines = [coords]
                    elif geom_dict["type"] == "MultiLineString":
                        lines = coords
                        
                    if not lines:
                        continue

                    for line_segment in lines:
                        if len(line_segment) < 2:
                            continue
                            
                        path_cells = set()
                        for i in range(len(line_segment) - 1):
                            start_lng, start_lat = line_segment[i]
                            end_lng, end_lat = line_segment[i+1]
                            
                            start_cell = h3.latlng_to_cell(start_lat, start_lng, resolution)
                            end_cell = h3.latlng_to_cell(end_lat, end_lng, resolution)
                            
                            try:
                                line_h3 = h3.grid_path_cells(start_cell, end_cell)
                                path_cells.update(line_h3)
                            except Exception:
                                path_cells.add(start_cell)
                                path_cells.add(end_cell)

                        for h3_index in path_cells:
                            if h3_index not in unique_hexagons:
                                unique_hexagons[h3_index] = _build_hexagon_feature(h3_index, {
                                    "ref": street.ref,
                                    "name": street.name,
                                    "type": "path_line"
                                })
                            
                except Exception as e:
                    logger.error(f"Falha ao processar rua {street.name}: {str(e)}")
                    continue

            return {"type": "FeatureCollection", "features": list(unique_hexagons.values())}

        except Exception as e:
            logger.error(f"Erro ao consultar ruas H3: {str(e)}")
            return {"type": "FeatureCollection", "features": []}
        finally:
            self.db.close()