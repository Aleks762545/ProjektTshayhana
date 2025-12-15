# Minimal schemas - not strictly used since routes accept dicts
from pydantic import BaseModel
from typing import List, Optional

class DishCreate(BaseModel):
    name: str
    description: Optional[str] = ''
    category: Optional[str] = 'main'
    price: float
    spice_level: int = 0
    is_vegan: bool = False
    ingredients: Optional[List[str]] = []
    image_path: Optional[str] = ''
    is_available: bool = True
