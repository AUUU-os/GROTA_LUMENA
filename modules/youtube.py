import logging
import asyncio
import json
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Dict, Any, List, Optional

logger = logging.getLogger("YT-MODULE")

class YouTubeModule:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
        }

    async def search_videos(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"đź“ş YouTube: Searching for '{query}'...")
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # search: prefix for yt-dlp
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch{max_results}:{query}", download=False))
                results = []
                if 'entries' in info:
                    for entry in info['entries']:
                        results.append({
                            "title": entry.get("title"),
                            "id": entry.get("id"),
                            "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                            "duration": entry.get("duration"),
                            "view_count": entry.get("view_count"),
                            "uploader": entry.get("uploader")
                        })
                return results
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
            return []

    async def get_transcript(self, video_id: str) -> Optional[str]:
        logger.info(f"đź“ş YouTube: Fetching transcript for {video_id}...")
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pl', 'en'])
            return " ".join([t['text'] for t in transcript_list])
        except Exception as e:
            logger.warning(f"Could not fetch transcript for {video_id}: {e}")
            return None

    async def summarize_video(self, video_id: str) -> str:
        transcript = await self.get_transcript(video_id)
        if not transcript:
            return "Transkrypt niedostÄ™pny. Nie mogÄ™ przygotowaÄ‡ podsumowania."
        
        # Integration with internal LLM (via ollama_bridge) would happen here
        from corex.ollama_bridge import ollama_bridge
        prompt = f"Podsumuj poniĹĽszy transkrypt filmu YouTube w 5 konkretnych punktach:\n\n{transcript[:4000]}"
        response = await ollama_bridge.generate(prompt=prompt, model="llama3")
        return response.get("response", "BĹ‚Ä…d generowania podsumowania.")

youtube_module = YouTubeModule()
