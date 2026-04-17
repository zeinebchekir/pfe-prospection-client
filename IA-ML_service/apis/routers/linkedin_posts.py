from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.apify_service import get_linkedin_posts

router = APIRouter()

class LinkedInPostsRequest(BaseModel):
    linkedin_url: str
    max_posts: int = 10

class LinkedInPostsResponse(BaseModel):
    linkedin_url: str
    posts: list | None
    total: int
    message: str

@router.post("/posts", response_model=LinkedInPostsResponse)
async def fetch_linkedin_posts(request: LinkedInPostsRequest):
    try:
        posts = get_linkedin_posts(request.linkedin_url, request.max_posts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not posts:
        raise HTTPException(
            status_code=404,
            detail="Aucun post trouvé pour cette entreprise"
        )

    return LinkedInPostsResponse(
        linkedin_url=request.linkedin_url,
        posts=posts,
        total=len(posts),
        message=f"✅ {len(posts)} posts récupérés"
    )