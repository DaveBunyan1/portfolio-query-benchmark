from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(String(1024), nullable=False)

    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821, UP037 # type: ignore
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    shares: Mapped[float] = mapped_column(Float)
    price_per_share: Mapped[float] = mapped_column(Float)
    transaction_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    user: Mapped[User] = relationship("User", back_populates="transactions")
