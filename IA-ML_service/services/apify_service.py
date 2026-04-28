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


def get_linkedin_informations(company_url: str):
    company_info={}
    endpoint = "https://api.apify.com/v2/acts/harvestapi~linkedin-company/run-sync-get-dataset-items"
    
    params = {
        "token": os.getenv("APIFY_API_TOKEN"),
        "format": "json"
    }
    
    # Exactement le même payload que l'interface Apify
    payload = {
        "companies": [company_url]
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
        info_response = response.json()
        if len(info_response) == 0:
            return None
        info=info_response[0]
        employee_range = info.get("employeeCountRange") or {}
        taille = (
            f"{employee_range.get('start', '?')}-{employee_range.get('end', '?')}"
            if employee_range else None
        )
        company_info["description"]=info.get("description")
        company_info["phone"]=info.get("phone").get("number") if info.get("phone") else None
        company_info["website"]=info.get("website")
        company_info["specialities"]=info.get("specialities")
        company_info["taille"]=taille
        company_info["date_creation_entreprise"]=info.get("foundedOn").get("year") if info.get("foundedOn") else None
        company_info["nb_locaux"]=len(info.get("locations")) if info.get("locations") else None
        print(f"✅ {len(info_response)} infos récupérés")
        return company_info
    else:
        raise Exception(f"Erreur: {response.status_code} - {response.text}")
              