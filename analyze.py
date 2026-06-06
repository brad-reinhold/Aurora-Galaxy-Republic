#!/usr/bin/env python3
"""
Comprehensive web crawler and content analyzer.
Extracts metadata, links, images, videos, and text from profiles, websites, and storage links.
Designed to build a searchable index for SEO and discoverability.
"""

import os
import re
import json
import time
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import hashlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from moviepy.editor import VideoFileClip
from pydub import AudioSegment

# Configuration
MAX_DEPTH = 4
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 0.7  # seconds between requests
MAX_REQUESTS_PER_DOMAIN = 60000
FAILED_LINKS_FILE = 'failed_domains.json'
CRAWL_CACHE_FILE = 'crawl_cache.json'

# Enhanced headers to bypass protection
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Create session with retry strategy
SESSION = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=0.7,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=['GET', 'HEAD']
)
adapter = HTTPAdapter(max_retries=retry_strategy)
SESSION.mount('http://', adapter)
SESSION.mount('https://', adapter)

class ContentAnalyzer:
    """Crawls and analyzes web content."""
    
    def __init__(self):
        self.visited_urls = set()
        self.failed_domains = self._load_json(FAILED_LINKS_FILE, {})
        self.cache = self._load_json(CRAWL_CACHE_FILE, {})
        self.all_content = []
        self.all_links = set()
        self.all_images = set()
        self.all_videos = set()
        self.all_audios = set()
    
    @staticmethod
    def _load_json(filename, default):
        """Load JSON file or return default."""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {filename}: {e}")
        return default
    
    @staticmethod
    def _save_json(filename, data):
        """Save data as JSON."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving {filename}: {e}")

    def should_skip_domain(self, url):
        """Check if domain has been marked as failed."""
        domain = urlparse(url).netloc
        return domain in self.failed_domains
    
    def mark_domain_failed(self, url, reason):
        """Mark a domain as failed and save it."""
        domain = urlparse(url).netloc
        if domain not in self.failed_domains:
            self.failed_domains[domain] = {
                'reason': reason,
                'first_failure': datetime.now().isoformat(),
                'count': 0
            }
        self.failed_domains[domain]['count'] += 1
        self._save_json(FAILED_LINKS_FILE, self.failed_domains)
    
    def check_domain_rate_limit(self, url):
        """Enforce per-domain rate limiting."""
        domain = urlparse(url).netloc
        if self.domain_request_count[domain] >= MAX_REQUESTS_PER_DOMAIN:
            return False
        self.domain_request_count[domain] += 1
        return True

    def fetch_content(self, url):
        """Fetch URL with domain-specific handling and retry logic."""
        if self.should_skip_domain(url):
            return None
        
        if not self.check_domain_rate_limit(url):
            print(f"⏱️  Rate limit reached for {urlparse(url).netloc}")
            return None
        
        # Check cache
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash in self.cache:
            cached = self.cache[url_hash]
            if (datetime.now().isoformat() < cached.get('expires', '2099-01-01')):
                return cached['data']
        
        try:
            print(f"🔄 Fetching: {url[:70]}...")
            response = SESSION.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # Cache successful response
            self.cache[url_hash] = {
                'data': response.text,
                'expires': datetime.now().isoformat()
            }
            self._save_json(CRAWL_CACHE_FILE, self.cache)

            return response.text
        
        except requests.exceptions.RequestException as e:
            self.mark_domain_failed(url, str(e))
            print(f"❌ Error fetching {url}: {e}")
        
        return None

    def extract_media(self, media_url):
        """Download and analyze audio/video files."""
        try:
            local_file = media_url.split('/')[-1]
            response = SESSION.get(media_url)
            if response.status_code == 200:
                with open(local_file, 'wb') as f:
                    f.write(response.content)
                
                if local_file.endswith(('.mp4', '.mov')):
                    self.all_videos.add(local_file)
                    clip = VideoFileClip(local_file)
                    duration = clip.duration  # Get video duration
                    print(f"Video {local_file} duration: {duration} seconds")
                    clip.close()
                elif local_file.endswith(('.mp3', '.wav')):
                    self.all_audios.add(local_file)
                    audio = AudioSegment.from_file(local_file)
                    duration = len(audio) / 1000
                    print(f"Audio {local_file} duration: {duration} seconds")
            else:
                print(f"Failed to download media: {media_url}")
        except Exception as e:
            print(f"Error processing media {media_url}: {e}")

    def extract_metadata(self, html, url):
        """Extract metadata from HTML."""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'title': '',
            'description': '',
            'images': [],
            'links': [],
            'videos': [],
            'audios': [],
            'text_preview': '',
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            metadata['title'] = soup.title.string if soup.title else 'No Title'
            metadata['description'] = soup.find("meta", {"name": "description"})['content'] if soup.find("meta", {"name": "description"}) else 'No Description'

            metadata['images'] = [urljoin(url, img['src']) for img in soup.find_all('img') if 'src' in img.attrs]
            metadata['links'] = [urljoin(url, link['href']) for link in soup.find_all('a', href=True)]
            
            # Extract media links
            metadata['videos'] = [urljoin(url, video['src']) for video in soup.find_all('video')]
            metadata['audios'] = [urljoin(url, audio['src']) for audio in soup.find_all('audio')]

            # Download and analyze media
            for media_url in metadata['videos']:
                self.extract_media(media_url)
            for media_url in metadata['audios']:
                self.extract_media(media_url)
            
        except Exception as e:
            print(f"Warning: Error extracting metadata from {url}: {e}")
        
        return metadata
    
    def crawl_url(self, url, depth=0):
        """Recursively crawl a URL and its nested links."""
        if url in self.visited_urls or depth > MAX_DEPTH:
            return
        
        self.visited_urls.add(url)
        
        html = self.fetch_content(url)
        if not html:
            return
        
        metadata = self.extract_metadata(html, url)
        self.all_content.append(metadata)
        
        # Crawl nested links at depth < MAX_DEPTH
        if depth < MAX_DEPTH:
            for link in metadata['links']:
                self.crawl_url(link, depth + 1)
    
    def load_seed_urls(self, filename):
        """Load seed URLs from a markdown file."""
        urls = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                urls = re.findall(r'https?://[^\s\)]+', content)
        except FileNotFoundError:
            print(f"Error: {filename} not found")
        return urls
    
    def generate_report(self):
        """Generate a comprehensive markdown report."""
        report = []
        report.append("# 📊 Comprehensive Web Analysis Report\n")
        report.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        report.append(f"## 📈 Summary\n")
        report.append(f"- **URLs Analyzed:** {len(self.all_content)}\n")
        report.append(f"- **Unique Links Found:** {len(self.all_links)}\n")
        report.append(f"- **Images Discovered:** {len(self.all_images)}\n")
        report.append(f"- **Videos Discovered:** {len(self.all_videos)}\n")
        report.append(f"- **Audios Discovered:** {len(self.all_audios)}\n")
        report.append(f"- **Failed Domains:** {len(self.failed_domains)}\n\n")
        
        # Failed domains
        if self.failed_domains:
            report.append("## ⚠️ Failed Domains (Excluded from Index)\n\n")
            for domain, info in sorted(self.failed_domains.items()):
                report.append(f"- `{domain}`: {info['reason']} (attempts: {info['count']})\n")
            report.append("\n")
        
        # Content index
        report.append("## 📑 Content Index\n\n")
        for item in self.all_content:
            report.append(f"### {item['title'] or item['url']}\n")
            report.append(f"**Source:** [`{item['domain']}`]({item['url']})\n")
            report.append(f"**Description:** {item['description']}\n")
            report.append(f"**Found Images:** {len(item['images'])}\n")
            report.append(f"**Found Videos:** {len(item['videos'])}\n")
            report.append(f"**Found Audios:** {len(item['audios'])}\n")
            report.append("---\n\n")
        
        return '\n'.join(report)
    
    def run(self, seed_file='links.md', output_file='analysis.md'):
        """Main execution."""
        print("\n🚀 Starting comprehensive web analysis...\n")
        
        seed_urls = self.load_seed_urls(seed_file)
        print(f"📌 Found {len(seed_urls)} seed URLs\n")
        
        for url in seed_urls:
            self.crawl_url(url)
        
        report = self.generate_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✅ Analysis complete!\n")
        print(f"📄 Report: {output_file}")
        print(f"⚠️  Failed: {FAILED_LINKS_FILE}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python analyze.py <api_key>")
        sys.exit(1)

    filmfreeway_api_key = sys.argv[1]
    analyzer = ContentAnalyzer()
    analyzer.run()
