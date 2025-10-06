from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.encoders import jsonable_encoder

from model.models import Sale, SaleItem, SaleStatus, PaymentStatus
from schema.sales import SaleCreate, SaleUpdate
from crud.inventory.crud_inventory_transaction import inventory_transaction
from core.exceptions import ValidationError
from ..base import CRUDBase

class CRUDSale(CRUDBase[Sale, SaleCreate, SaleUpdate]):
    async def create_sale(
        self,
        db: AsyncSession,
        *,
        tenant_id: int,
        obj_in: SaleCreate
    ) -> Sale:
        """Create a new sale with items and corresponding inventory transactions"""
        try:
            # Start a transaction
            obj_in_data = jsonable_encoder(obj_in)
            items = obj_in_data.pop("items", [])
            
            if not items:
                raise ValidationError("At least one item is required")

            # Generate reference number
            ref_num = f"SALE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Create sale record
            sale = Sale(
                tenant_id=tenant_id,
                reference_number=ref_num,
                status=SaleStatus.DRAFT,
                payment_status=PaymentStatus.UNPAID,
                **obj_in_data
            )
            
            db.add(sale)
            await db.flush()  # Get the sale ID without committing

            # Process items and create inventory transactions
            subtotal = 0
            total_tax = 0
            total_discount = 0

            for item_data in items:
                quantity = item_data["quantity"]
                unit_price = item_data["unit_price"]
                discount_percent = item_data.get("discount_percent", 0)
                tax_percent = item_data.get("tax_percent", 0)

                # Calculate item totals
                item_subtotal = quantity * unit_price
                discount_amount = (item_subtotal * discount_percent) / 100
                tax_amount = ((item_subtotal - discount_amount) * tax_percent) / 100
                item_total = item_subtotal - discount_amount + tax_amount

                # Create sale item
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=item_data["product_id"],
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_percent=discount_percent,
                    discount_amount=discount_amount,
                    tax_percent=tax_percent,
                    tax_amount=tax_amount,
                    subtotal=item_subtotal,
                    total=item_total
                )
                db.add(sale_item)

                # Create inventory transaction
                await inventory_transaction.create_transaction(
                    db,
                    tenant_id=tenant_id,
                    product_id=item_data["product_id"],
                    warehouse_id=obj_in_data["warehouse_id"],
                    transaction_type="STOCK_OUT",
                    quantity=quantity,
                    reference_number=f"{ref_num}-{sale_item.id}",
                    notes=f"Sale: {ref_num}"
                )

                # Update totals
                subtotal += item_subtotal
                total_tax += tax_amount
                total_discount += discount_amount

            # Update sale totals
            sale.subtotal = subtotal
            sale.tax_amount = total_tax
            sale.discount_amount = total_discount
            sale.total_amount = subtotal - total_discount + total_tax
            sale.balance_amount = sale.total_amount

            await db.commit()
            await db.refresh(sale)
            return sale

        except Exception as e:
            await db.rollback()
            raise ValidationError(f"Failed to create sale: {str(e)}")

    async def update_status(
        self,
        db: AsyncSession,
        *,
        sale_id: int,
        tenant_id: int,
        new_status: SaleStatus
    ) -> Sale:
        """Update the status of a sale"""
        sale = await self.get(db, id=sale_id)
        if not sale or sale.tenant_id != tenant_id:
            raise ValidationError("Sale not found")

        #Idempotency: if you’re already in that status, do nothing and return immediately.
        if sale.status == new_status:
            return sale

        # Validate status transition

            #You define the finite-state machine: for each current status, which next statuses are allowed.

            # COMPLETED/CANCELLED have empty lists → they’re terminal (no outgoing edges).
        valid_transitions = {
            SaleStatus.DRAFT: [SaleStatus.PENDING, SaleStatus.CANCELLED],
            SaleStatus.PENDING: [SaleStatus.CONFIRMED, SaleStatus.CANCELLED],
            SaleStatus.CONFIRMED: [SaleStatus.COMPLETED, SaleStatus.CANCELLED],
            SaleStatus.COMPLETED: [],
            SaleStatus.CANCELLED: []
        }

        # Enforces the FSM: if the new_status isn’t in the allowed list for the current status, throw a domain error.

        if new_status not in valid_transitions[sale.status]:
            raise ValidationError(f"Invalid status transition from {sale.status.name} to {new_status.name}, You can only transition to: {valid_transitions[sale.status]}.")

        sale.status = new_status
        sale.updated_at = datetime.utcnow()

        db.add(sale)
        await db.commit()
        await db.refresh(sale)
        return sale

    async def update_payment(
        self,
        db: AsyncSession,
        *,
        sale_id: int,
        tenant_id: int,
        amount: float,
        payment_method: str
    ) -> Sale:
        """Record a payment for a sale"""
        sale = await self.get(db, id=sale_id)
        if not sale or sale.tenant_id != tenant_id:
            raise ValidationError("Sale not found")

        if sale.status not in [SaleStatus.CONFIRMED, SaleStatus.COMPLETED]:
            raise ValidationError("Can only process payments for confirmed or completed sales")

        if amount <= 0:
            raise ValidationError("Payment amount must be greater than zero")

        if sale.paid_amount + amount > sale.total_amount:
            raise ValidationError("Payment amount exceeds remaining balance")

        # Update payment details
        sale.paid_amount += amount
        sale.balance_amount = sale.total_amount - sale.paid_amount
        sale.payment_method = payment_method
        sale.updated_at = datetime.utcnow()

        # Update payment status
        if sale.paid_amount >= sale.total_amount:
            sale.payment_status = PaymentStatus.PAID
        elif sale.paid_amount > 0:
            sale.payment_status = PaymentStatus.PARTIALLY_PAID

        db.add(sale)
        await db.commit()
        await db.refresh(sale)
        return sale

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[SaleStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        sale_date_gte: Optional[datetime] = None,
        sale_date_lte: Optional[datetime] = None
    ) -> List[Sale]:
        """Get multiple sales with various filters"""
        conditions = []
        
        if tenant_id is not None:
            conditions.append(Sale.tenant_id == tenant_id)
        if customer_id is not None:
            conditions.append(Sale.customer_id == customer_id)
        if user_id is not None:
            conditions.append(Sale.user_id == user_id)
        if status is not None:
            conditions.append(Sale.status == status)
        if payment_status is not None:
            conditions.append(Sale.payment_status == payment_status)
        if sale_date_gte is not None:
            conditions.append(Sale.sale_date >= sale_date_gte)
        if sale_date_lte is not None:
            conditions.append(Sale.sale_date <= sale_date_lte)

        statement = (
            select(Sale)
            .where(and_(*conditions))
            .offset(skip)
            .limit(limit)
            .order_by(Sale.created_at.desc())
        )

        result = await db.execute(statement)
        return result.scalars().all()

    async def get_user_sales(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        tenant_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[SaleStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Sale]:
        """Get all sales created by a specific user"""
        return await self.get_multi(
            db,
            skip=skip,
            limit=limit,
            tenant_id=tenant_id,
            user_id=user_id,
            status=status,
            payment_status=payment_status,
            sale_date_gte=start_date,
            sale_date_lte=end_date
        )

sale = CRUDSale(Sale)