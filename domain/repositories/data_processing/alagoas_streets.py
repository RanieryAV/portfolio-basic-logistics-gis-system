from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import Column, Integer, String
from domain.config.database_config import Base


class AlagoasStreets(Base):
    """
    SQLAlchemy model representing the 'alagoas-streets.geojson' dataset.
    Stores OSM street layouts as MultiLineStrings.
    """

    __tablename__ = "alagoas_streets"
    __table_args__ = {"schema": "logistics_gis"}

    primary_key = Column(Integer, primary_key=True, autoincrement=True)

    # Matching the specific properties found in the JSON file
    ref = Column(String(50), nullable=True)
    postal_cod = Column(String(50), nullable=True)
    name = Column(String(255), nullable=True)
    nm_mun = Column(String(255), nullable=True)
    bairro = Column(String(255), nullable=True)

    # Streets are generally LineStrings or MultiLineStrings
    geom = Column(Geometry(geometry_type="MULTILINESTRING", srid=4326), nullable=False)

    def to_dict(self):
        geom_shape = to_shape(self.geom) if self.geom is not None else None

        return {
            "type": "Feature",
            "properties": {
                "ref": self.ref,
                "postal_cod": self.postal_cod,
                "name": self.name,
                "NM_MUN": self.nm_mun,
                "Bairro": self.bairro,
            },
            "geometry": geom_shape.__geo_interface__ if geom_shape else None,
        }
