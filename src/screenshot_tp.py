import sys
import os
import requests
from dotenv import load_dotenv
load_dotenv()

def run(tweet_url: str, output_path: str):
    api_key = os.environ.get("TWEET_PIK_API_KEY")
    api_url = "https://tweetpik.com/api/v2/images"

    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key
    }

    payload = {
        "url": tweet_url,
        "displayMetrics": False,
        "displayEmbeds": False,
        "contentWidth": 120,
        "displayVerified": True
    }

    print("🔁 Sending request to Tweetpik API...")
    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code != 200 and response.status_code != 201:
        print("❌ Failed to fetch image metadata:", response.status_code, response.text)
        sys.exit(1)

    image_url = response.json().get("url")
    if not image_url:
        print("❌ Image URL not found in response.")
        sys.exit(1)

    print(f"📥 Downloading image from: {image_url}")
    image_response = requests.get(image_url)

    if image_response.status_code != 200:
        print("❌ Failed to download image:", image_response.status_code)
        sys.exit(1)

    with open(output_path, "wb") as f:
        f.write(image_response.content)

    print(f"✅ Image saved to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python screenshot_api.py <Twitter URL> <Output Path>")
        sys.exit(1)

    tweet_url = sys.argv[1]
    output_path = sys.argv[2]

    run(tweet_url, output_path)
