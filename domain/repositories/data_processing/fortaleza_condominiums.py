from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import Column, Integer, String, Text, Float, UniqueConstraint
from domain.config.database_config import Base

class FortalezaCondominiums(Base):

    __tablename__ = "fortaleza_condominiums"

    __table_args__ = (
        UniqueConstraint(
            "condominium_name",
            "geom",
            name="unique_condominium_name_geom"
        ),
        {
            "schema": "logistics_gis"
        },
    )

    primary_key = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    condominium_id = Column(
        String(255),
        nullable=False
    )

    condominium_name = Column(
        String(255),
        nullable=False
    )

    cartography = Column(
        String(255),
        nullable=False
    )

    address = Column(
        String(255),
        nullable=False
    )

    age = Column(
        Integer,
        nullable=False
    )

    total_number_of_elevators = Column(
        Integer,
        nullable=False
    )

    latitude = Column(
        Float,
        nullable=False
    )

    longitude = Column(
        Float,
        nullable=False
    )

    geom = Column(
        Geometry(
            geometry_type="POINT",
            srid=4326
        ),
        nullable=False
    )

    construction_standard_name = Column(
        String(255),
        nullable=False
    )

    use_type = Column(
        String(255),
        nullable=False
    )

    condominium_type = Column(
        String(255),
        nullable=False
    )

    total_number_of_units = Column(
        Integer,
        nullable=False
    )

    total_number_of_units_per_floor = Column(
        Integer,
        nullable=False
    )

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        point_shape = (
            to_shape(self.geom)
            if self.geom is not None
            else None
        )

        point_wkt = (
            point_shape.wkt
            if point_shape
            else None
        )

        return {
            "primary_key": self.primary_key,
            "condominium_id": self.condominium_id,
            "condominium_name": self.condominium_name,
            "cartography": self.cartography,
            "address": self.address,
            "age": self.age,
            "total_number_of_elevators": self.total_number_of_elevators,
            "total_number_of_units_per_floor": self.total_number_of_units_per_floor,
            "total_number_of_units": self.total_number_of_units,
            "condominium_type": self.condominium_type,
            "use_type": self.use_type,
            "construction_standard_name": self.construction_standard_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "geom": point_wkt
        }