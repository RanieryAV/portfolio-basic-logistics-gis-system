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

# GLOBAL MEMORY CACHE TO AVOID H3 RECALCULATIONS
_H3_CACHE = {}

def _build_hexagon_feature(h3_index: str, properties: dict) -> dict:
    """
    Internal utility to convert an H3 index into a native GeoJSON Polygon (dictionary).
    """
    boundary = h3.cell_to_boundary(h3_index)
    
    # GeoJSON requires (longitude, latitude) order and a closed ring
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
    Service responsible for fetching postal agencies from PostGIS 
    and converting them into an H3 hexagonal grid (Points).
    """
    def __init__(self):
        self.db = SessionLocal()

    def execute(self, resolution: int = 8):
        cache_key = f"agencies_{resolution}"
        if cache_key in _H3_CACHE:
            return _H3_CACHE[cache_key]

        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS logistics_gis"))
            self.db.commit()
            Base.metadata.create_all(bind=engine)

            # Uses ST_X and ST_Y similar to QueryPostalAgenciesService
            agencies_data = self.db.query(
                PostalAgencies,
                func.ST_X(PostalAgencies.location).label("longitude"),
                func.ST_Y(PostalAgencies.location).label("latitude")
            ).all()

            unique_hexagons = {}
            for agency, longitude, latitude in agencies_data:
                try:
                    # latlng_to_cell processes the isolated point coordinates
                    h3_index = h3.latlng_to_cell(latitude, longitude, resolution)
                    
                    if h3_index not in unique_hexagons:
                        agency_dict = agency.to_dict()
                        unique_hexagons[h3_index] = _build_hexagon_feature(h3_index, {
                            "name": agency_dict.get("name"),
                            "city": agency_dict.get("city"),
                            "type": "point_agency"
                        })
                except Exception as e:
                    logger.error(f"Failed to generate H3 for agency {agency.name}: {str(e)}")
                    continue
                    
            result = {"type": "FeatureCollection", "features": list(unique_hexagons.values())}
            _H3_CACHE[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Error querying H3 agencies: {str(e)}")
            return {"type": "FeatureCollection", "features": []}
        finally:
            self.db.close()


class QueryH3NeighborhoodsService:
    """
    Service responsible for fetching neighborhood boundaries from PostGIS 
    and filling them with an H3 hexagonal grid (Polygons).
    """
    def __init__(self):
        self.db = SessionLocal()

    def execute(self, resolution: int = 8):
        cache_key = f"neighborhoods_{resolution}"
        if cache_key in _H3_CACHE:
            return _H3_CACHE[cache_key]

        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS logistics_gis"))
            self.db.commit()
            Base.metadata.create_all(bind=engine)

            # Transforms geometry directly into GeoJSON text in the database
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
                    # H3 requires (latitude, longitude) order for its internal polygon
                    if geom_dict["type"] == "Polygon":
                        outer_boundary = [(lat, lng) for lng, lat in coords[0]]
                    elif geom_dict["type"] == "MultiPolygon":
                        outer_boundary = [(lat, lng) for lng, lat in coords[0][0]]
                    
                    if not outer_boundary:
                        continue

                    h3_poly = h3.LatLngPoly(outer_boundary)
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
                    logger.error(f"Failed to process polygon {area.code}: {str(e)}")
                    continue

            result = {"type": "FeatureCollection", "features": list(unique_hexagons.values())}
            _H3_CACHE[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Error querying H3 neighborhoods: {str(e)}")
            return {"type": "FeatureCollection", "features": []}
        finally:
            self.db.close()


class QueryH3AlagoasStreetsService:
    """
    Service responsible for fetching the street network, expanding it 
    via ST_Buffer in the database and applying H3 hexagons (Lines).
    """
    def __init__(self):
        self.db = SessionLocal()

    def execute(self, resolution: int = 8, buffer_degrees: float = None):
        cache_key = f"streets_{resolution}"
        if cache_key in _H3_CACHE:
            return _H3_CACHE[cache_key]

        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS logistics_gis"))
            self.db.commit()
            Base.metadata.create_all(bind=engine)

            # ST_Buffer transforms LineString into Polygon at runtime
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
                    logger.error(f"Failed to process street {street.name}: {str(e)}")
                    continue

            result = {"type": "FeatureCollection", "features": list(unique_hexagons.values())}
            _H3_CACHE[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Error querying H3 streets: {str(e)}")
            return {"type": "FeatureCollection", "features": []}
        finally:
            self.db.close()