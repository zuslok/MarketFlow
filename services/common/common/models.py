from sqlalchemy import Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint, Date, Text
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from datetime import datetime, timezone, date
from typing import List, Optional

class Base(DeclarativeBase):
    pass

class Symbol(Base):
    """Definitions of followed symbols (BTCUSDT, AMZN vb.)"""
    __tablename__ = "symbols"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    prices: Mapped[List["Price"]] = relationship("Price", back_populates="symbol_rel", cascade="all, delete-orphan")
    metrics: Mapped[List["DailyMetric"]] = relationship("DailyMetric", back_populates="symbol_rel", cascade="all, delete-orphan")

class Price(Base):
    """Time series price data"""
    __tablename__ = "prices"
    __table_args__ = (
        UniqueConstraint("symbol_id", "ts", name="uq_symbol_ts"),
    )
    
    index: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    open: Mapped[Optional[float]] = mapped_column(Float)
    high: Mapped[Optional[float]] = mapped_column(Float)
    low: Mapped[Optional[float]] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[Optional[float]] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    inserted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    symbol_rel: Mapped["Symbol"] = relationship("Symbol", back_populates="prices")

class DailyMetric(Base):
    """Calculated daily metrics like moving averages"""
    __tablename__ = "daily_metrics"
    __table_args__ = (
        UniqueConstraint("symbol_id", "date", name="uq_symbol_date"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    ma_20: Mapped[Optional[float]] = mapped_column(Float)
    ma_50: Mapped[Optional[float]] = mapped_column(Float)
    rsi_14: Mapped[Optional[float]] = mapped_column(Float)
    volatility_20: Mapped[Optional[float]] = mapped_column(Float)
    daily_return: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    symbol_rel: Mapped["Symbol"] = relationship("Symbol", back_populates="metrics")

class ETLJob(Base):
    """Tracking ETL job statuses"""
    __tablename__ = "etl_jobs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
