from pydantic import BaseModel
from typing import Optional

# Define the request model
class QueryRequest(BaseModel):
    spec_number: Optional[str] = None
    version_number: Optional[str] = None
    section_number: Optional[str] = None
    query: str