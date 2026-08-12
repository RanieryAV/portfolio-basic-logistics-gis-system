from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from domain.config.database_config import Base

class FortalezaDistricts(Base):
    __tablename__ = "fortaleza_districts"
    __table_args__ = (
        UniqueConstraint("code", name="unique_neighborhood_code"),
        {"schema": "logistics_gis"},
    )

    primary_key = Column(Integer, primary_key=True, autoincrement=True)
    district_id = Column(String(50), nullable=False)
    active_autonomous_units_count = Column(Integer, nullable=True)
    blocked_autonomous_units_count = Column(Integer, nullable=True)
    total_calculated_tax_amount = Column(Float, nullable=True)
    total_due_tax_amount = Column(Float, nullable=True)
    blocks_count = Column(Integer, nullable=True)
    total_building_area = Column(Float, nullable=True)
    district_area = Column(Float, nullable=True)

    
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
                "district_id": self.district_id,
                "active_autonomous_units_count": self.active_autonomous_units_count,
                "blocked_autonomous_units_count": self.blocked_autonomous_units_count,
                "total_calculated_tax_amount": self.total_calculated_tax_amount,
                "total_due_tax_amount": self.total_due_tax_amount,
                "blocks_count": self.blocks_count,
                "total_building_area": self.total_building_area,
                "district_area": self.district_area,
            },
            "geometry": geom_shape.__geo_interface__ if geom_shape else None
        }