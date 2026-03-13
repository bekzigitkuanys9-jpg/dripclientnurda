from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, Product, Key, Purchase
import asyncio

async def process_purchase(session: AsyncSession, user: User, product_id: int) -> tuple[bool, str]:
    """
    Business logic for purchasing a product.
    Returns (success: bool, message: str)
    """
    # 1. Check Product exists
    product_result = await session.execute(select(Product).where(Product.id == product_id))
    product = product_result.scalar_one_or_none()
    
    if not product:
        return False, "Product not found."
    
    # 2. Check balance
    if user.balance < product.price:
        return False, "Insufficient balance. Please top-up."
        
    # 3. Find available key
    key_result = await session.execute(
        select(Key).where(Key.product_id == product_id, Key.is_used == False).with_for_update().limit(1)
    )
    key = key_result.scalar_one_or_none()
    
    if not key:
        return False, "No available keys for this product."
        
    # 4. Deduct balance and total_spent
    user.balance -= product.price
    user.total_spent += product.price
    
    # 5. Mark key as used
    key.is_used = True
    key.used_by = user.tg_id
    
    # 6. Record purchase
    purchase = Purchase(
        user_tg_id=user.tg_id,
        product_id=product_id,
        key_id=key.id,
        price=product.price
    )
    session.add(purchase)
    
    # Commit changes
    await session.commit()
    
    # Send Key message details back
    return True, f"Here is your key for {product.name}:\n<code>{key.key_value}</code>"
