from pydantic import AwareDatetime, BaseModel

class ScheduleCreate(BaseModel):
    scheduled_at: AwareDatetime
    
class VariantEdit(BaseModel):
    text: str

class PostCreate(BaseModel):
    markdown: str