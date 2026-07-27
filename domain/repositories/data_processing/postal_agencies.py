from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import Column, Integer, String, Text, Float, UniqueConstraint
from domain.config.database_config import Base

class PostalAgencies(Base):

    __tablename__ = "postal_agencies"

    __table_args__ = (
        UniqueConstraint(
            "name",
            "zip_code",
            name="unique_name_zip_code"
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

    name = Column(
        String(255),
        nullable=False
    )

    address = Column(
        Text,
        nullable=False
    )

    city = Column(
        String(255),
        nullable=False
    )

    state = Column(
        String(2),
        nullable=False
    )

    zip_code = Column(
        String(15),
        nullable=False
    )

    phone = Column(
        String(80),
        nullable=True
    )

    latitude = Column(
        Float,
        nullable=False
    )

    longitude = Column(
        Float,
        nullable=False
    )

    location = Column(
        Geometry(
            geometry_type="POINT",
            srid=4326
        ),
        nullable=False
    )

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        point_shape = (
            to_shape(self.location)
            if self.location is not None
            else None
        )

        point_wkt = (
            point_shape.wkt
            if point_shape
            else None
        )

        return {
            "primary_key": self.primary_key,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "phone": self.phone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location": point_wkt
        }