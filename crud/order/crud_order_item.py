from typing import List, Optional
from sqlmodel import Session, select
from model.models import OrderItem
from schema import OrderItemCreate, OrderItemUpdate
from ..base import CRUDBase

class CRUDOrderItem(CRUDBase[OrderItem, OrderItemCreate, OrderItemUpdate]):
    def get_by_order(
        self,
        db: Session,
        *,
        order_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrderItem]:
        query = (
            select(self.model)
            .where(self.model.order_id == order_id)
            .offset(skip)
            .limit(limit)
        )
        return db.exec(query).all()

    def get_by_product(
        self,
        db: Session,
        *,
        product_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrderItem]:
        query = (
            select(self.model)
            .where(self.model.product_id == product_id)
            .offset(skip)
            .limit(limit)
        )
        return db.exec(query).all()

    def calculate_order_total(self, db: Session, *, order_id: int) -> float:
        query = select(func.sum(self.model.total_price)).where(self.model.order_id == order_id)
        result = db.exec(query).first()
        return result[0] if result[0] is not None else 0.0

order_item = CRUDOrderItem(OrderItem)