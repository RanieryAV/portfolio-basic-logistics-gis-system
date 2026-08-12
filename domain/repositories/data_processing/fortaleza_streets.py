from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import Column, Integer, String
from domain.config.database_config import Base

class FortalezaStreets(Base):
    
    __tablename__ = "fortaleza_streets"
    __table_args__ = {"schema": "logistics_gis"}

    primary_key = Column(Integer, primary_key=True, autoincrement=True)
    
    # Matching the specific properties found in the JSON file
    public_place_cod = Column(String(50), nullable=True)
    public_place_name = Column(String(255), nullable=True)
    type = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    starts_at_neighbourhood = Column(String(255), nullable=True)
    ends_at_neighbourhood = Column(String(255), nullable=True)
    total_number_of_street_sections = Column(Integer, nullable=True)
    street_length = Column(Integer, nullable=True)
    building_autonomous_units_count = Column(Integer, nullable=True)
    land_autonomous_units_count = Column(Integer, nullable=True)
    residential_autonomous_units_count = Column(Integer, nullable=True)
    non_residential_autonomous_units_count = Column(Integer, nullable=True)
    lots_count = Column(Integer, nullable=True)
    created_at = Column(String(255), nullable=True)
    updated_at = Column(String(255), nullable=True)
    public_place_starts_at = Column(String(255), nullable=True)
    public_place_ends_at = Column(String(255), nullable=True)
    street_direction = Column(String(255), nullable=True)

    
    # Streets are generally LineStrings or MultiLineStrings
    geom = Column(
        Geometry(geometry_type="MULTILINESTRING", srid=4326),
        nullable=False
    )

    def to_dict(self):
        geom_shape = to_shape(self.geom) if self.geom is not None else None
        
        return {
            "type": "Feature",
            "properties": {
                "public_place_cod": self.public_place_cod,
                "public_place_name": self.public_place_name,
                "type": self.type,
                "full_name": self.full_name,
                "starts_at_neighbourhood": self.starts_at_neighbourhood,
                "ends_at_neighbourhood": self.ends_at_neighbourhood,
                "total_number_of_street_sections": self.total_number_of_street_sections,
                "street_length": self.street_length,
                "building_autonomous_units_count": self.building_autonomous_units_count,
                "land_autonomous_units_count": self.land_autonomous_units_count,
                "residential_autonomous_units_count": self.residential_autonomous_units_count,
                "non_residential_autonomous_units_count": self.non_residential_autonomous_units_count,
                "lots_count": self.lots_count,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "public_place_starts_at": self.public_place_starts_at,
                "public_place_ends_at": self.public_place_ends_at,
                "street_direction": self.street_direction
            },
            "geometry": geom_shape.__geo_interface__ if geom_shape else None
        }