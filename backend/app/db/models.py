from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CoffeeShop(Base):
    __tablename__ = "coffee_shops"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    
    external_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True, index=True)

    opening_hours: Mapped[str | None] = mapped_column(String, nullable=True)
    has_wifi: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
