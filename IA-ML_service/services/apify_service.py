import requests
import os
def get_linkedin_posts(company_url: str, max_posts: int = 10):
    posts=[]
    endpoint = "https://api.apify.com/v2/acts/harvestapi~linkedin-company-posts/run-sync-get-dataset-items"
    
    params = {
        "token": os.getenv("APIFY_API_TOKEN"),
        "format": "json"
    }
    
    # Exactement le même payload que l'interface Apify
    payload = {
        "includeQuotePosts": True,
        "includeReposts": True,
        "maxComments": 5,
        "maxPosts": max_posts,
        "maxReactions": 5,
        "postNestedComments": False,
        "postNestedReactions": False,
        "scrapeComments": False,
        "scrapeReactions": False,
        "targetUrls": [company_url]
    }
    
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(
        endpoint,
        params=params,
        json=payload,
        headers=headers,
        timeout=120
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code in [200, 201]:
        posts_response = response.json()
        if len(posts_response) == 0:
            return None
        for post in posts_response:
            posts.append(post.get("content"))
        print(f"✅ {len(posts)} posts récupérés")
        return posts
    else:
        raise Exception(f"Erreur: {response.status_code} - {response.text}")
      