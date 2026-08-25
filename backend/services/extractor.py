import re
import httpx
import trafilatura
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.proxies import WebshareProxyConfig
import pymupdf as fitz
import os

def detect_source_type(url: str) -> str:
    url = url.lower()
    if "youtube.com/watch" in url or "youtu.be/" in url:
        return "youtube"
    elif "twitter.com" in url or "x.com" in url:
        return "tweet"
    elif "instagram.com" in url:
        return "instagram"
    elif url.endswith(".pdf"):
        return "pdf"
    else:
        return "article"

def extract_youtube_id(url: str) -> str:
    patterns = [
        r'youtube\.com/watch\?v=([^&]+)',
        r'youtu\.be/([^?]+)',
        r'youtube\.com/embed/([^?]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def extract_youtube(url: str) -> dict:
    video_id = extract_youtube_id(url)
    if not video_id:
        return {"title": "YouTube Video", "content": "", "error": "Could not extract video ID"}
    
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.fetch(video_id)
        transcript = " ".join([t.text for t in transcript_list])
        transcript = transcript[:8000]
        
        return {
            "title": f"YouTube Video ({video_id})",
            "content": transcript,
            "source_type": "youtube"
        }
    except Exception as e:
        # Try fetching page title at least
        try:
            import httpx
            response = httpx.get(
                f"https://www.youtube.com/watch?v={video_id}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=10
            )
            import re
            title_match = re.search(r'<title>(.*?)</title>', response.text)
            title = title_match.group(1).replace(' - YouTube', '') if title_match else f"YouTube Video ({video_id})"
            
            return {
                "title": title,
                "content": f"YouTube video: {title}. Video ID: {video_id}. Auto-transcript unavailable on server.",
                "source_type": "youtube"
            }
        except:
            return {
                "title": f"YouTube Video ({video_id})",
                "content": f"YouTube video ID: {video_id}",
                "source_type": "youtube"
            }

def extract_article(url: str) -> dict:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {"title": "Article", "content": "", "error": "Could not fetch URL"}
        
        content = trafilatura.extract(
            downloaded,
            include_title=True,
            include_comments=False,
            include_tables=False
        )
        
        if not content:
            return {"title": "Article", "content": "", "error": "Could not extract content"}
        
        # Get title separately
        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if metadata and metadata.title else "Article"
        
        # Limit to 8000 chars
        content = content[:8000]
        
        return {
            "title": title,
            "content": content,
            "source_type": "article"
        }
    except Exception as e:
        return {"title": "Article", "content": "", "error": str(e)}

def extract_pdf(file_bytes: bytes) -> dict:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        
        # Limit to 8000 chars
        text = text[:8000]
        
        return {
            "title": "PDF Document",
            "content": text,
            "source_type": "pdf"
        }
    except Exception as e:
        return {"title": "PDF", "content": "", "error": str(e)}

def extract_instagram(url: str) -> dict:
    # Instagram blocks scraping — user provides their own note
    return {
        "title": "Instagram Reel",
        "content": "",
        "source_type": "instagram",
        "needs_annotation": True
    }

def extract_tweet(url: str) -> dict:
    try:
        # Basic extraction via trafilatura
        downloaded = trafilatura.fetch_url(url)
        content = trafilatura.extract(downloaded) if downloaded else ""
        
        return {
            "title": "Tweet/Thread",
            "content": content[:8000] if content else "",
            "source_type": "tweet"
        }
    except Exception as e:
        return {"title": "Tweet", "content": "", "error": str(e)}

def extract_content(url: str, file_bytes: bytes = None) -> dict:
    try:
        source_type = detect_source_type(url)
        
        if source_type == "youtube":
            result = extract_youtube(url)
        elif source_type == "article":
            result = extract_article(url)
        elif source_type == "pdf" and file_bytes:
            result = extract_pdf(file_bytes)
        elif source_type == "instagram":
            result = extract_instagram(url)
        elif source_type == "tweet":
            result = extract_tweet(url)
        else:
            result = extract_article(url)
        
        result["source_type"] = source_type
        return result
    except Exception as e:
        return {
            "title": "Unknown",
            "content": "",
            "source_type": "other",
            "error": str(e)
        }