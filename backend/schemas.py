from pydantic import BaseModel

class JobCreate(BaseModel):
    keyword: str
    location: str
    radius: int
    grid_size: str = "10x10"

class JobResponse(BaseModel):
    job_id: str
    status: str
