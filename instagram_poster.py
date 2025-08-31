import os
import requests

# ---------------- CONFIG ----------------
IG_SHORT_LIVED_TOKEN = os.getenv("IG_ACCESS_TOKEN")  # short-lived token (~1 hour)
APP_CLIENT_SECRET = os.getenv("APP_CLIENT_SECRET")        # from your Facebook App
IG_USER_ID = os.getenv("IG_USER_ID")                # numeric IG User ID
print("IG_USER_ID:", IG_USER_ID)
# IMAGE_URL = "https://your-public-image-url.com/image.jpg"
# CAPTION = "🔥 BMW E46 — an icon of the early 2000s. Affordable at launch, a legend today!"


# ---------- STEP 0: Exchange short-lived token for long-lived ----------
def get_long_lived_token(short_lived_token: str, client_secret: str):
    url = "https://graph.instagram.com/access_token"
    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": client_secret,
        "access_token": short_lived_token
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    return data["access_token"], data.get("expires_in", 0)


# ---------- STEP 1: Create media container ----------
def create_media_container(image_url: str, caption: str, access_token: str):
    url = f"https://graph.facebook.com/v23.0/{IG_USER_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    container_id = r.json().get("id")
    if not container_id:
        raise ValueError(f"No container ID returned: {r.json()}")
    return container_id


# ---------- STEP 2: Publish media ----------
def publish_media(container_id: str, access_token: str):
    url = f"https://graph.facebook.com/v23.0/{IG_USER_ID}/media_publish"
    payload = {"creation_id": container_id}
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post(url, json=payload, headers=headers)
    r.raise_for_status()
    return r.json()


# ---------- MAIN FUNCTION ----------
def post_to_instagram(image_url: str, caption: str):
    try:
        # Exchange token
        # long_lived_token, expires_in = get_long_lived_token(IG_SHORT_LIVED_TOKEN, APP_CLIENT_SECRET)
        # print(f"✅ Long-lived token obtained (expires in {expires_in} seconds)")

        # Create container
        container_id = create_media_container(image_url, caption, IG_SHORT_LIVED_TOKEN)
        print(f"✅ Media container created: {container_id}")

        # Publish media
        result = publish_media(container_id, IG_SHORT_LIVED_TOKEN)
        print("✅ Successfully posted to Instagram!")
        print(result)
        return result

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ Upload failed: {http_err}")
        if http_err.response is not None:
            print("Response:", http_err.response.text)
        return None
    except Exception as e:
        print("❌ Unexpected error posting to Instagram:", e)
        return None


# # ---------- RUN EXAMPLE ----------
# if __name__ == "__main__":
#     post_to_instagram(IMAGE_URL, CAPTION)
