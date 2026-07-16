from domain.config.database_config import db
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import UniqueConstraint


class PostalAgencies(db.Model):

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

    primary_key = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    name = db.Column(
        db.String(255),
        nullable=False
    )

    address = db.Column(
        db.Text,
        nullable=False
    )

    district = db.Column(
        db.String(255),
        nullable=True
    )

    city = db.Column(
        db.String(255),
        nullable=False
    )

    state = db.Column(
        db.String(2),
        nullable=False
    )

    zip_code = db.Column(
        db.String(15),
        nullable=False
    )

    phone = db.Column(
        db.String(80),
        nullable=True
    )

    latitude = db.Column(
        db.Float,
        nullable=False
    )

    longitude = db.Column(
        db.Float,
        nullable=False
    )

    location = db.Column(
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

            "district": self.district,

            "city": self.city,

            "state": self.state,

            "zip_code": self.zip_code,

            "phone": self.phone,

            "latitude": self.latitude,

            "longitude": self.longitude,

            "location": point_wkt
        }