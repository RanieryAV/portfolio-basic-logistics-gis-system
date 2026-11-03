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

            # Utiliza ST_X e ST_Y idêntico ao QueryPostalAgenciesService
            agencies_data = self.db.query(
                PostalAgencies,
                func.ST_X(PostalAgencies.location).label("longitude"),
                func.ST_Y(PostalAgencies.location).label("latitude")
            ).all()

            features = []
            for agency, longitude, latitude in agencies_data:
                try:
                    # latlng_to_cell processa as coordenadas isoladas do ponto
                    h3_index = h3.latlng_to_cell(latitude, longitude, resolution)
                    
                    agency_dict = agency.to_dict()
                    features.append(_build_hexagon_feature(h3_index, {
                        "name": agency_dict.get("name"),
                        "city": agency_dict.get("city"),
                        "type": "point_agency"
                    }))
                except Exception as e:
                    logger.error(f"Falha ao gerar H3 para agência {agency.name}: {str(e)}")
                    continue
                    
            return {"type": "FeatureCollection", "features": features}

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
                func.ST_AsGeoJSON(Neighborhoods.geom).label("geojson_geom")
            ).all()

            features = []
            for area, geojson_str in neighborhoods_data:
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

                    for h3_index in h3_indices:
                        features.append(_build_hexagon_feature(h3_index, {
                            "code": area.code,
                            "name": area.name,
                            "type": "polygon_area"
                        }))
                except Exception as e:
                    logger.error(f"Falha ao processar polígono {area.code}: {str(e)}")
                    continue

            return {"type": "FeatureCollection", "features": features}

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

    def execute(self, resolution: int = 8, buffer_degrees: float = 0.0002):
        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS logistics_gis"))
            self.db.commit()
            Base.metadata.create_all(bind=engine)

            # ST_Buffer transforma a LineString em Polygon em tempo de execução
            streets_data = self.db.query(
                AlagoasStreets,
                func.ST_AsGeoJSON(func.ST_Buffer(AlagoasStreets.geom, buffer_degrees)).label("geojson_geom")
            ).all()

            features = []
            for street, geojson_str in streets_data:
                try:
                    if not geojson_str:
                        continue
                    
                    geom_dict = json.loads(geojson_str)
                    coords = geom_dict.get("coordinates", [])
                    
                    outer_boundary = []
                    if geom_dict["type"] == "Polygon":
                        outer_boundary = [(lat, lng) for lng, lat in coords[0]]
                    elif geom_dict["type"] == "MultiPolygon":
                        outer_boundary = [(lat, lng) for lng, lat in coords[0][0]]
                        
                    if not outer_boundary:
                        continue

                    h3_poly = h3.Polygon(outer_boundary)
                    h3_indices = h3.polygon_to_cells(h3_poly, resolution)

                    for h3_index in h3_indices:
                        features.append(_build_hexagon_feature(h3_index, {
                            "ref": street.ref,
                            "name": street.name,
                            "type": "buffered_line"
                        }))
                except Exception as e:
                    logger.error(f"Falha ao processar rua {street.name}: {str(e)}")
                    continue

            return {"type": "FeatureCollection", "features": features}

        except Exception as e:
            logger.error(f"Erro ao consultar ruas H3: {str(e)}")
            return {"type": "FeatureCollection", "features": []}
        finally:
            self.db.close()