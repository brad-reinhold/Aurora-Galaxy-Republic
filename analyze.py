#!/usr/bin/env python3
"""
Comprehensive web crawler and content analyzer.
Extracts metadata, links, images, and text from all profiles, websites, and storage links.
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

# Configuration
MAX_DEPTH = 2
REQUEST_TIMEOUT = 15
RATE_LIMIT_DELAY = 0.3  # seconds between requests
MAX_REQUESTS_PER_DOMAIN = 50
FAILED_LINKS_FILE = 'failed_domains.json'
CRAWL_CACHE_FILE = 'crawl_cache.json'

# Enhanced headers to bypass protection
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}

# Domain-specific configurations
DOMAIN_CONFIGS = {
    'instagram.com': {
        'headers': {**HEADERS, 'Referer': 'https://www.instagram.com/'},
        'delay': 1.0,
        'retries': 5
    },
    'filmfreeway.com': {
        'headers': {**HEADERS, 'Referer': 'https://www.filmfreeway.com/'},
        'delay': 1.5,
        'retries': 5
    },
    'dropbox.com': {
        'headers': {**HEADERS, 'Referer': 'https://www.dropbox.com/'},
        'delay': 0.5,
        'retries': 3
    },
    'proton.me': {
        'headers': {**HEADERS},
        'delay': 0.5,
        'retries': 3
    },
    'drive.proton.me': {
        'headers': {**HEADERS},
        'delay': 0.5,
        'retries': 3
    },
    'tiktok.com': {
        'headers': {**HEADERS, 'Referer': 'https://www.tiktok.com/'},
        'delay': 1.5,
        'retries': 5
    },
    'facebook.com': {
        'headers': {**HEADERS, 'Referer': 'https://www.facebook.com/'},
        'delay': 1.0,
        'retries': 4
    },
}

# Create session with retry strategy
SESSION = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=['GET', 'HEAD']
)
adapter = HTTPAdapter(max_retries=retry_strategy)
SESSION.mount('http://', adapter)
SESSION.mount('https://', adapter)


class ContentAnalyzer:
    """Crawls and analyzes web content with special handling for protected domains."""
    
    def __init__(self):
        self.visited_urls = set()
        self.failed_domains = self._load_json(FAILED_LINKS_FILE, {})
        self.cache = self._load_json(CRAWL_CACHE_FILE, {})
        self.domain_request_count = defaultdict(int)
        self.all_content = []
        self.all_links = set()
        self.all_images = set()
    
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
    
    def get_url_hash(self, url):
        """Get a hash of the URL for caching."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get_domain_config(self, url):
        """Get domain-specific configuration."""
        domain = urlparse(url).netloc
        base_domain = domain.replace('www.', '')
        
        # Check exact match first
        if domain in DOMAIN_CONFIGS:
            return DOMAIN_CONFIGS[domain]
        # Then check base domain
        for key in DOMAIN_CONFIGS:
            if key in domain or domain in key:
                return DOMAIN_CONFIGS[key]
        
        # Return default config
        return {
            'headers': HEADERS,
            'delay': RATE_LIMIT_DELAY,
            'retries': 3
        }
    
    def fetch_content(self, url):
        """Fetch URL with domain-specific handling and retry logic."""
        if self.should_skip_domain(url):
            return None
        
        if not self.check_domain_rate_limit(url):
            print(f"⏱️  Rate limit reached for {urlparse(url).netloc}")
            return None
        
        # Check cache
        url_hash = self.get_url_hash(url)
        if url_hash in self.cache:
            cached = self.cache[url_hash]
            if (datetime.now().isoformat() < cached.get('expires', '2099-01-01')):
                print(f"✓ Cache hit: {url[:60]}...")
                return cached['data']
        
        domain_config = self.get_domain_config(url)
        headers = domain_config['headers']
        delay = domain_config['delay']
        
        try:
            print(f"🔄 Fetching: {url[:70]}...")
            
            # Add delay before request
            time.sleep(delay)
            
            # Attempt request with retry logic
            response = SESSION.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                verify=True
            )
            
            # Handle common blocking status codes
            if response.status_code == 403:
                print(f"⚠️  HTTP 403 (Forbidden): {url} - Trying alternative approach...")
                # Try with different user agent
                alt_headers = {**headers, 'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'}
                time.sleep(delay)
                response = SESSION.get(url, headers=alt_headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            
            if response.status_code == 429:
                print(f"⚠️  HTTP 429 (Rate Limited): {url} - Waiting before retry...")
                time.sleep(5)
                response = SESSION.get(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            
            response.raise_for_status()
            
            # Cache successful response
            self.cache[url_hash] = {
                'data': response.text,
                'expires': datetime.now().isoformat()
            }
            self._save_json(CRAWL_CACHE_FILE, self.cache)
            
            return response.text
        
        except requests.exceptions.Timeout:
            self.mark_domain_failed(url, 'Timeout')
            print(f"❌ Timeout: {url}")
        except requests.exceptions.HTTPError as e:
            self.mark_domain_failed(url, f'HTTP {e.response.status_code}')
            print(f"❌ HTTP Error {e.response.status_code}: {url}")
        except requests.exceptions.ConnectionError:
            self.mark_domain_failed(url, 'Connection error')
            print(f"❌ Connection error: {url}")
        except Exception as e:
            self.mark_domain_failed(url, str(type(e).__name__))
            print(f"❌ Error fetching {url}: {e}")
        
        return None
    
    def extract_metadata(self, html, url):
        """Extract metadata from HTML."""
        from bs4 import BeautifulSoup
        
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'title': '',
            'description': '',
            'images': [],
            'links': [],
            'text_preview': '',
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title_tag = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'twitter:title'})
            if title_tag:
                metadata['title'] = title_tag.get('content', '')
            if not metadata['title']:
                title_elem = soup.find('title')
                if title_elem:
                    metadata['title'] = title_elem.get_text(strip=True)
            
            # Extract description
            desc_tag = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                metadata['description'] = desc_tag.get('content', '')
            
            # Extract images
            for img in soup.find_all('img', limit=10):
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    full_img_url = urljoin(url, img_url)
                    metadata['images'].append(full_img_url)
                    self.all_images.add(full_img_url)
            
            # Extract links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').strip()
                if href.startswith(('http://', 'https://')):
                    metadata['links'].append(href)
                    self.all_links.add(href)
                elif href.startswith('/'):
                    full_url = urljoin(url, href)
                    metadata['links'].append(full_url)
                    self.all_links.add(full_url)
            
            # Extract text preview
            body = soup.find('body')
            if body:
                text = ' '.join(body.get_text(separator=' ').split())
                metadata['text_preview'] = text[:500]
            
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
        print(f"✓ Analyzed: {metadata['title'][:50] if metadata['title'] else 'Unknown'}")
        
        # Crawl nested links at depth < MAX_DEPTH
        if depth < MAX_DEPTH:
            for link in list(metadata['links'])[:5]:
                if link not in self.visited_urls:
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
        report.append(f"- **Failed Domains:** {len(self.failed_domains)}\n\n")
        
        # Failed domains
        if self.failed_domains:
            report.append("## ⚠️ Failed Domains (Excluded from Index)\n\n")
            for domain, info in sorted(self.failed_domains.items()):
                report.append(f"- `{domain}`: {info['reason']} (attempts: {info['count']})\n")
            report.append("\n")
        
        # Content index
        report.append("## 📑 Content Index\n\n")
        for item in sorted(self.all_content, key=lambda x: x['domain']):
            report.append(f"### {item['title'] or item['url']}\n\n")
            report.append(f"**Source:** [`{item['domain']}`]({item['url']})\n\n")
            
            if item['description']:
                report.append(f"**Description:** {item['description']}\n\n")
            
            if item['images']:
                report.append(f"**Media:** {len(item['images'])} images\n\n")
            
            if item['links']:
                report.append(f"**Linked Pages:** {len(item['links'])}\n\n")
            
            if item['text_preview']:
                report.append(f"**Preview:** {item['text_preview'][:150]}...\n\n")
            
            report.append("---\n\n")
        
        # Links inventory
        report.append("## 🔗 All Discovered Links\n\n")
        for link in sorted(self.all_links):
            report.append(f"- {link}\n")
        
        # Images inventory
        if self.all_images:
            report.append("\n## 🖼️ All Images\n\n")
            for img in sorted(self.all_images):
                report.append(f"- {img}\n")
        
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
        print(f"💾 Cache: {CRAWL_CACHE_FILE}")
        print(f"⚠️  Failed: {FAILED_LINKS_FILE}")


if __name__ == "__main__":
    analyzer = ContentAnalyzer()
    analyzer.run()
