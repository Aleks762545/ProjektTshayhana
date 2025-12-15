from pydantic import BaseModel
from typing import List, Optional

class OrderItem(BaseModel):
    dish_id: int
    quantity: int

class OrderCreate(BaseModel):
    table_number: str
    items: List[OrderItem]
    guest_phone: Optional[str] = None
