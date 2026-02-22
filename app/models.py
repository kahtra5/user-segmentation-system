# ORM models
from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from sqlalchemy import Column, Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import relationship

from sqlalchemy import Index

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class UserMetrics(Base):
    __tablename__ = "user_metrics"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    total_orders = Column(Integer, default=0)
    orders_last_7_days = Column(Integer, default=0)
    orders_last_23_days = Column(Integer, default=0)
    orders_last_30_days = Column(Integer, default=0)

    lifetime_value = Column(Numeric(12, 2), default=0)

    location = Column(String(100), nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", backref="metrics")

Index("idx_user_metrics_orders_23d", UserMetrics.orders_last_23_days)
Index("idx_user_metrics_orders_30d", UserMetrics.orders_last_30_days)
Index("idx_user_metrics_ltv", UserMetrics.lifetime_value)
Index("idx_user_metrics_location", UserMetrics.location)


class Segment(Base):
    __tablename__ = "segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    rule_definition = Column(JSONB, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

class UserSegment(Base):
    __tablename__ = "user_segments"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    segment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("segments.id", ondelete="CASCADE"),
        primary_key=True,
    )

    assigned_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(150), nullable=False)

    target_segment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("segments.id", ondelete="CASCADE"),
        nullable=False,
    )

    status = Column(String(20), default="ACTIVE")  # ACTIVE / PAUSED

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

class ExperimentVariant(Base):
    __tablename__ = "experiment_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String(100), nullable=False)

    weight = Column(Integer, nullable=False)

    config = Column(JSONB, nullable=False)


class ExperimentAssignment(Base):
    __tablename__ = "experiment_assignments"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        primary_key=True,
    )

    variant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("experiment_variants.id"),
        nullable=False,
    )

    assigned_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    amount = Column(Numeric(12, 2), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )