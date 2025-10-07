from sqlmodel.ext.asyncio.session import AsyncSession
from model.models import Sale, SaleItem, SaleStatus, PaymentStatus
from datetime import datetime

async def create_test_sale(
    session: AsyncSession,
    tenant_id: int,
    items_count: int = 2
) -> Sale:
    """
    Create a test sale with the specified number of items.
    Returns the created sale.
    """
    # Create sale
    sale = Sale(
        tenant_id=tenant_id,
        customer_id=1,  # Test customer
        warehouse_id=1,  # Test warehouse
        reference_number=f"TEST-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        status=SaleStatus.DRAFT,
        payment_status=PaymentStatus.UNPAID,
        sale_date=datetime.utcnow(),
        subtotal=0,
        tax_amount=0,
        discount_amount=0,
        total_amount=0,
        balance_amount=0,
        paid_amount=0
    )
    session.add(sale)
    await session.flush()

    # Create sale items
    subtotal = 0
    for i in range(items_count):
        unit_price = 10.0 * (i + 1)  # Different prices for each item
        quantity = i + 1
        item_subtotal = unit_price * quantity
        
        item = SaleItem(
            sale_id=sale.id,
            product_id=i + 1,  # Using incrementing product IDs
            quantity=quantity,
            unit_price=unit_price,
            discount_percent=0,
            tax_percent=0,
            discount_amount=0,
            tax_amount=0,
            subtotal=item_subtotal,
            total=item_subtotal
        )
        session.add(item)
        subtotal += item_subtotal

    # Update sale totals
    sale.subtotal = subtotal
    sale.total_amount = subtotal
    sale.balance_amount = subtotal

    await session.commit()
    await session.refresh(sale)
    return sale