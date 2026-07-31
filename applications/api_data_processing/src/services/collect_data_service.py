import json
import os
import logging
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text
from domain.config.database_config import SessionLocal, engine, Base
from domain.repositories.data_processing.postal_agencies import PostalAgencies

logger = logging.getLogger(__name__)


class IngestPostalAgenciesService:
    """
    Service responsible for reading a local GeoJSON file and ingesting
    its data into the PostGIS database via bulk UPSERT operations.
    """

    def __init__(self):
        # Instantiate the database session when the service is called
        self.db = SessionLocal()

    def execute(self, batch_size: int = 100):
        """
        Executes the ingestion pipeline.

        Args:
            batch_size (int): The maximum number of records to process in a single bulk UPSERT.
        """
        try:
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS logistics_gis"))
            self.db.commit()

            # Security: Create SQLAlchemy tables in PostGIS if they don't exist yet
            Base.metadata.create_all(bind=engine)

            current_dir = os.path.dirname(os.path.abspath(__file__))
            local_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))

            # Smart path resolution: Docker volumes vs Local execution
            possible_paths = [
                "/app/datasets/correios_al.geojson",  # Docker volume mapping
                "/app/datasets/correios_al.geojson.json",  # Docker volume mapping (Fallback)
                os.path.join(
                    local_root, "shared", "utils", "datasets", "correios_al.geojson"
                ),  # Local execution
                os.path.join(
                    local_root,
                    "shared",
                    "utils",
                    "datasets",
                    "correios_al.geojson.json",
                ),  # Local execution (Fallback)
            ]

            geojson_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    geojson_path = path
                    break

            if not os.path.exists(geojson_path):
                raise FileNotFoundError(f"GeoJSON file not found at: {geojson_path}")

            with open(geojson_path, "r", encoding="utf-8") as file:
                geo_data = json.load(file)

            features = geo_data.get("features", [])
            total_processed = 0
            batch_data = []

            # We define the statement outside the loop for bulk execution
            stmt = insert(PostalAgencies)

            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["name", "zip_code"],
                set_={
                    "address": stmt.excluded.address,
                    "city": stmt.excluded.city,
                    "state": stmt.excluded.state,
                    "phone": stmt.excluded.phone,
                    "latitude": stmt.excluded.latitude,
                    "longitude": stmt.excluded.longitude,
                    "location": stmt.excluded.location,
                },
            )

            for feature in features:
                props = feature.get("properties", {})
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates", [0, 0])

                # WKT Format required by PostGIS/GeoAlchemy2 (Longitude, Latitude)
                wkt_point = f"SRID=4326;POINT({coords[0]} {coords[1]})"

                # Split City/State coming from the GeoJSON (e.g., "ÁGUA BRANCA/AL")
                city_state = props.get("Cidade", "").split("/")
                city = city_state[0].strip() if len(city_state) > 0 else "Unknown"
                state = city_state[1].strip() if len(city_state) > 1 else "AL"

                # Append the dictionary matching the SQLAlchemy columns
                batch_data.append(
                    {
                        "name": props.get("Nome"),
                        "address": props.get("Endereço"),
                        "city": city,
                        "state": state,
                        "zip_code": props.get("CEP"),
                        "phone": props.get("Telefone"),
                        "latitude": coords[1],
                        "longitude": coords[0],
                        "location": wkt_point,
                    }
                )

                if len(batch_data) >= batch_size:
                    self.db.execute(upsert_stmt, batch_data)
                    total_processed += len(batch_data)
                    batch_data.clear()  # Empty the batch list for the next iteration

            if batch_data:
                self.db.execute(upsert_stmt, batch_data)
                total_processed += len(batch_data)
                batch_data.clear()

            self.db.commit()

            logger.info(
                f"Successfully processed {total_processed} postal agencies in batches of {batch_size}."
            )

            return {
                "status": "success",
                "message": f"{total_processed} Postal Agencies processed via GeoJSON in batches of {batch_size}.",
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error ingesting postal agencies: {str(e)}")
            raise e
        finally:
            self.db.close()


class QueryPostalAgenciesService:
    """
    Service responsible for querying the PostGIS database for all saved
    postal agencies and returning them formatted as a GeoJSON FeatureCollection.
    """

    def __init__(self):
        self.db = SessionLocal()

    def execute(self):
        """
        Executes the query and formats the output. Gracefully handles errors
        by returning an empty FeatureCollection if the database is unavailable
        or the table doesn't exist yet.
        """
        try:
            agencies = self.db.query(PostalAgencies).all()
            features = []

            for agency in agencies:
                agency_dict = agency.to_dict()

                # Using the raw latitude and longitude floats already saved in the database
                features.append(
                    {
                        "type": "Feature",
                        "properties": {
                            "Name": agency_dict.get("name"),
                            "Address": agency_dict.get("address"),
                            "City": agency_dict.get("city"),
                            "State": agency_dict.get("state"),
                            "ZIP Code": agency_dict.get("zip_code"),
                            "Phone": agency_dict.get("phone"),
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [
                                agency_dict.get("longitude"),
                                agency_dict.get("latitude"),
                            ],
                        },
                    }
                )

            return {"type": "FeatureCollection", "features": features}

        except Exception as e:
            logger.error(f"Error querying postal agencies: {str(e)}")
            return {"type": "FeatureCollection", "features": []}
        finally:
            self.db.close()
