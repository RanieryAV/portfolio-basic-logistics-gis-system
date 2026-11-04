import json
import os
import logging
import h3
from shapely.geometry import shape
from sqlalchemy.dialects.postgresql import insert, JSONB
from sqlalchemy import text, func, cast, literal_column, Text
from domain.config.database_config import SessionLocal, engine, Base
from domain.repositories.data_processing.postal_agencies import PostalAgencies
from domain.repositories.data_processing.neighborhoods import Neighborhoods
from domain.repositories.data_processing.alagoas_streets import AlagoasStreets

logger = logging.getLogger(__name__)

# GLOBAL MEMORY CACHE TO AVOID RECALCULATIONS
_H3_CACHE = {}

class QueryH3PostalAgenciesService:
    """
    Service responsible for fetching postal agencies from PostGIS 
    and converting them into native H3 hexagonal cells (Points) via h3-pg.
    """
    def __init__(self):
        self.db = SessionLocal()

    def execute(self, resolution: int = 8):
        cache_key = f"agencies_{resolution}"
        if cache_key in _H3_CACHE:
            return _H3_CACHE[cache_key]

        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS prototype_gis"))
            self.db.commit()
            Base.metadata.create_all(bind=engine)

            # Uses h3_lat_lng_to_cell to generate the H3 index from the point,
            # and h3_cell_to_boundary_geometry to extract the hexagon polygon.
            h3_index_expr = func.h3_lat_lng_to_cell(PostalAgencies.location, resolution)
            
            hex_subq = self.db.query(
                h3_index_expr.label("h3_index"),
                func.h3_cell_to_boundary_geometry(h3_index_expr).label("geom"),
                PostalAgencies.name,
                PostalAgencies.city
            ).distinct(h3_index_expr).subquery("hex")

            geojson_feature = func.jsonb_build_object(
                'type', 'Feature',
                'geometry', cast(func.ST_AsGeoJSON(hex_subq.c.geom), JSONB),
                'properties', func.jsonb_build_object(
                    'h3_index', cast(hex_subq.c.h3_index, Text),
                    'name', hex_subq.c.name,
                    'city', hex_subq.c.city,
                    'type', 'point_agency'
                )
            )

            feature_collection_query = self.db.query(
                func.jsonb_build_object(
                    'type', 'FeatureCollection',
                    'features', func.coalesce(func.jsonb_agg(geojson_feature), cast('[]', JSONB))
                )
            )

            result = feature_collection_query.scalar()
            
            if not result:
                return {"type": "FeatureCollection", "features": []}

            feature_collection = result if isinstance(result, dict) else json.loads(result)
            _H3_CACHE[cache_key] = feature_collection
            return feature_collection

        except Exception as e:
            logger.error(f"Error querying H3 agencies: {str(e)}")
            return {"type": "FeatureCollection", "features": []}
        finally:
            self.db.close()


class QueryH3NeighborhoodsService:
    """
    Service responsible for fetching neighborhood boundaries from PostGIS 
    and filling them with an H3 hexagonal grid (Polygons) via h3-pg.
    """
    def __init__(self):
        self.db = SessionLocal()

    def execute(self, resolution: int = 8):
        cache_key = f"neighborhoods_{resolution}"
        if cache_key in _H3_CACHE:
            return _H3_CACHE[cache_key]

        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS prototype_gis"))
            self.db.commit()
            Base.metadata.create_all(bind=engine)

            query = text("""
                SELECT jsonb_build_object(
                    'type', 'FeatureCollection',
                    'features', COALESCE(jsonb_agg(
                        jsonb_build_object(
                            'type', 'Feature',
                            'geometry', CAST(ST_AsGeoJSON(hex.geom) AS JSONB),
                            'properties', jsonb_build_object(
                                'h3_index', CAST(hex.h3_index AS TEXT),
                                'code', hex.code,
                                'name', hex.name,
                                'type', 'polygon_area'
                            )
                        )
                    ), CAST('[]' AS JSONB))
                ) AS geojson
                FROM (
                    SELECT DISTINCT ON (cells.h3_index)
                        cells.h3_index AS h3_index,
                        h3_cell_to_boundary_geometry(cells.h3_index) AS geom,
                        n.code,
                        n.name
                    FROM prototype_gis.neighborhoods n
                    CROSS JOIN LATERAL ST_Dump(n.geom) AS poly
                    CROSS JOIN LATERAL h3_polygon_to_cells(poly.geom, :resolution) AS cells(h3_index)
                ) AS hex;
            """)

            result = self.db.execute(query, {"resolution": resolution}).scalar()
            
            if not result:
                return {"type": "FeatureCollection", "features": []}
                
            feature_collection = result if isinstance(result, dict) else json.loads(result)
            _H3_CACHE[cache_key] = feature_collection
            return feature_collection

        except Exception as e:
            logger.error(f"Error querying H3 neighborhoods: {str(e)}")
            return {"type": "FeatureCollection", "features": []}
        finally:
            self.db.close()


class QueryH3AlagoasStreetsService:
    """
    Service responsible for fetching the street network, expanding it 
    via ST_Buffer in the database and applying H3 hexagons (Lines) via h3-pg.
    """
    def __init__(self):
        self.db = SessionLocal()

    def execute(self, resolution: int = 8, buffer_degrees: float = None):
        cache_key = f"streets_{resolution}_{buffer_degrees}"
        if cache_key in _H3_CACHE:
            return _H3_CACHE[cache_key]

        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS prototype_gis"))
            self.db.commit()
            Base.metadata.create_all(bind=engine)

            buffer_val = buffer_degrees if buffer_degrees is not None else 0.0001

            query = text("""
                SELECT jsonb_build_object(
                    'type', 'FeatureCollection',
                    'features', COALESCE(jsonb_agg(
                        jsonb_build_object(
                            'type', 'Feature',
                            'geometry', CAST(ST_AsGeoJSON(hex.geom) AS JSONB),
                            'properties', jsonb_build_object(
                                'h3_index', CAST(hex.h3_index AS TEXT),
                                'ref', hex.ref,
                                'name', hex.name,
                                'type', 'path_line'
                            )
                        )
                    ), CAST('[]' AS JSONB))
                ) AS geojson
                FROM (
                    SELECT DISTINCT ON (cells.h3_index)
                        cells.h3_index AS h3_index,
                        h3_cell_to_boundary_geometry(cells.h3_index) AS geom,
                        s.ref,
                        s.name
                    FROM prototype_gis.alagoas_streets s
                    CROSS JOIN LATERAL ST_Buffer(s.geom, :buffer_val) AS buffered_geom
                    CROSS JOIN LATERAL ST_Dump(buffered_geom) AS poly
                    CROSS JOIN LATERAL h3_polygon_to_cells(poly.geom, :resolution) AS cells(h3_index)
                ) AS hex;
            """)

            result = self.db.execute(query, {"resolution": resolution, "buffer_val": buffer_val}).scalar()
            
            if not result:
                return {"type": "FeatureCollection", "features": []}
                
            feature_collection = result if isinstance(result, dict) else json.loads(result)
            _H3_CACHE[cache_key] = feature_collection
            return feature_collection

        except Exception as e:
            logger.error(f"Error querying H3 streets: {str(e)}")
            return {"type": "FeatureCollection", "features": []}
        finally:
            self.db.close()