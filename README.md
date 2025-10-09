# Tweet to Reel

**Tweet to Reel** converts tweets into vertical videos or formatted screenshots for Instagram, TikTok, and other platforms.

> [!NOTE]  
> For local run the web app supports photo processing only. \
> You can create videos using the run_all script. \
> To use CUDA processing locally, refer to [CUDA worker container](https://github.com/Costinbc/tweet-to-reel-worker)

This project is a work in progress. Current features include:

- Capture a screenshot of a tweet
- Crop and clean up the tweet image
- Download video content from the tweet
- Combine image and video into a 1080x1920 reel using FFmpeg
- Reels can have white, black, or blurred backgrounds
- Progress status and estimated time remaining
- Generate static tweet images sized for Instagram (1080x1350)
- Mobile-friendly web interface with download links

### Requirements
- Orshot API key for tweet screenshot generation

### How to Use

You can run the project in two ways:

- Via script:
  ```
  python src/run_all.py <result_type> <background_type> [<reel_layout>] [<crop>] <tweet_url>
  ```
  result_type: video/photo \
  background_type: white/blur \
  reel_layout: video_top/video_bottom - not needed if result_type is photo \
  crop: cropped/uncropped - not needed if result_type is photo

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


### Known limitations

- No retry feature for failed steps.
- Local run limited to photo generation with the web app or running in Docker terminal using the worker repo.
- No mobile app; results must first be downloaded, then saved to the gallery.

### Planned features/fixes

- Retry feature for failed steps

More features and improvements coming soon.
