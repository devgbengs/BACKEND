import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from model.models import Sale, SaleItem, SaleStatus
from tests.utils.auth import create_test_user
from tests.utils.sales import create_test_sale

@pytest.mark.asyncio
async def test_delete_sale_with_items(
    client: AsyncClient,
    session: AsyncSession
):
    """Test that deleting a sale properly removes all associated items"""
    # Create a test user
    user = await create_test_user(session)
    
    # Create a test sale with items
    sale = await create_test_sale(session, user.tenant_id)
    
    # Verify initial state
    statement = select(SaleItem).where(SaleItem.sale_id == sale.id)
    result = await session.execute(statement)
    items = result.scalars().all()
    assert len(items) > 0, "Sale should have items"
    
    # Delete the sale
    response = await client.delete(
        f"/api/v1/sales/{sale.id}",
        headers={"Authorization": f"Bearer {user.token}"}
    )
    assert response.status_code == 200
    
    # Verify sale is deleted
    statement = select(Sale).where(Sale.id == sale.id)
    result = await session.execute(statement)
    deleted_sale = result.scalars().first()
    assert deleted_sale is None
    
    # Verify all items are deleted
    statement = select(SaleItem).where(SaleItem.sale_id == sale.id)
    result = await session.execute(statement)
    remaining_items = result.scalars().all()
    assert len(remaining_items) == 0

@pytest.mark.asyncio
async def test_cannot_delete_non_draft_sale(
    client: AsyncClient,
    session: AsyncSession
):
    """Test that only draft sales can be deleted"""
    # Create a test user
    user = await create_test_user(session)
    
    # Create a test sale with non-draft status
    sale = await create_test_sale(session, user.tenant_id)
    sale.status = SaleStatus.PENDING
    session.add(sale)
    await session.commit()
    await session.refresh(sale)
    
    # Attempt to delete the sale
    response = await client.delete(
        f"/api/v1/sales/{sale.id}",
        headers={"Authorization": f"Bearer {user.token}"}
    )
    assert response.status_code == 400
    assert "Can only delete draft sales" in response.json()["detail"]
    
    # Verify sale still exists
    statement = select(Sale).where(Sale.id == sale.id)
    result = await session.execute(statement)
    existing_sale = result.scalars().first()
    assert existing_sale is not None