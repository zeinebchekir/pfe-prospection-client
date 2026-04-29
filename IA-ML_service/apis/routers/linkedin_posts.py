from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.apify_service import get_linkedin_posts, get_linkedin_informations

router = APIRouter()

class LinkedInPostsRequest(BaseModel):
    linkedin_url: str
    max_posts: int = 10
class LinkedInInfosRequest(BaseModel):
    linkedin_url: str
   
class LinkedInPostsResponse(BaseModel):
    linkedin_url: str
    posts: list | None
    total: int
    message: str

class LinkedInInfosResponse(BaseModel):
    linkedin_url: str
    infos: dict | None
    total: int
    message: str



@router.post("/posts", response_model=LinkedInPostsResponse)
async def fetch_linkedin_posts(request: LinkedInPostsRequest):
    try:
        posts = get_linkedin_posts(request.linkedin_url, request.max_posts)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    if not posts:
        raise HTTPException(
            status_code=404,
            detail="Aucun post trouvé pour cette entreprise"
        )
    print(posts)
    return LinkedInPostsResponse(
        linkedin_url=request.linkedin_url,
        posts=posts,
        total=len(posts),
        message=f"✅ {len(posts)} posts récupérés"
    )

@router.post("/informations", response_model=LinkedInInfosResponse)
async def fetch_linkedin_posts(request: LinkedInInfosRequest):
    try:
        infos = get_linkedin_informations(request.linkedin_url)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    if not infos:
        raise HTTPException(
            status_code=404,
            detail="Aucune information trouvé pour cette entreprise"
        )
    print(infos)
    return LinkedInInfosResponse(
        linkedin_url=request.linkedin_url,
        infos=infos,
        total=len(infos),
        message=f"✅ {len(infos)} infos récupérés"
    )


