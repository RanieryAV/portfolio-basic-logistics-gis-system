from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from domain.config.database_config import Base

class Neighborhoods(Base):
    __tablename__ = "neighborhoods"
    __table_args__ = (
        UniqueConstraint("code", name="unique_neighborhood_code"),
        {"schema": "logistics_gis"},
    )

    primary_key = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    state = Column(String(255), nullable=True)
    area_km2 = Column(Float, nullable=True)
    
    geom = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326),
        nullable=False
    )

    def to_dict(self):
        # Convert WKB element back to a Shapely shape, then to GeoJSON dict
        geom_shape = to_shape(self.geom) if self.geom is not None else None
        
        return {
            "type": "Feature",
            "properties": {
                "CD_BAIRRO": self.code,
                "NM_BAIRRO": self.name,
                "NM_MUN": self.city,
                "NM_UF": self.state,
                "AREA_KM2": self.area_km2
            },
            "geometry": geom_shape.__geo_interface__ if geom_shape else None
        }