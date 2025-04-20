# Tweet to Reel

**Tweet to Reel** converts tweets into vertical videos or formatted screenshots for Instagram, TikTok, and other platforms.

This project is a work in progress. Current features include:

- Capture a screenshot of a tweet
- Crop and clean up the tweet image
- Download video content from the tweet
- Combine image and video into a 1080x1920 reel using FFmpeg
- Reels can either have white or blurred backgrounds
- Generate static tweet images sized for Instagram (1080x1350)
- Mobile-friendly web interface with download links

### How to Use

You can run the project in two ways:

- Via script:
  ```
  python src/run_all.py <result_type> [<reel_type>] <tweet_url>
  ```
  result_type: video/photo
  reel_type: white/blur - not needed if result_type is photo

- Using the web app:
  ```
  flask -A src/app.py run
  ```
  
### Tech Stack

- Python (OpenCV, Pillow, yt-dlp)
- FFmpeg for video rendering
- Flask for the web interface
- Deployed on Google Cloud Run
- Currently hosted at [tweet-to-reel.com](https://tweet-to-reel.com)

More features and improvements coming soon.
