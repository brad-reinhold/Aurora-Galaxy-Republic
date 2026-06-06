import os
import re
import requests
from pymediainfo import MediaInfo
from bs4 import BeautifulSoup

def find_links_in_page(url):
    links = []
    try:
        response = requests.get(url)
        if response.ok:
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                soup = BeautifulSoup(response.text, 'html.parser')
                for link in soup.find_all('a', href=True):
                    full_url = link['href']
                    if full_url.startswith(('http://', 'https://')):
                        links.append(full_url)
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {e}")
    return links

def find_links_in_file(file_path):
    links = []
    with open(file_path, 'r') as file:
        content = file.read()
        links = re.findall(r'(https?://[^\s]+)', content)
    return links

def analyze_media(file_url):
    try:
        response = requests.get(file_url)
        file_path = file_url.split('/')[-1]

        with open(file_path, 'wb') as f:
            f.write(response.content)

        media_info = MediaInfo.parse(file_path)
        metadata = {
            'title': '',
            'duration': '',
            'format': '',
            'size': len(response.content),
            'error': None
        }

        for track in media_info.tracks:
            if track.track_type == "General":
                metadata['title'] = track.title or file_path
                metadata['duration'] = track.duration
                metadata['format'] = track.format
                break

        return metadata

    except Exception as e:
        return {'error': str(e)}

def generate_report(links):
    report_lines = ["# Comprehensive Analysis Report\n"]
    
    for link in links:
        analysis_result = analyze_media(link)
        report_lines.append(f"## Link: {link}\n")
        if analysis_result.get('error'):
            report_lines.append(f"**Error:** {analysis_result['error']}\n")
        else:
            report_lines.append(f"- **Title:** {analysis_result['title']}\n")
            report_lines.append(f"- **Duration:** {analysis_result['duration']} ms\n")
            report_lines.append(f"- **Format:** {analysis_result['format']}\n")
            report_lines.append(f"- **Size:** {analysis_result['size']} bytes\n")
        report_lines.append("\n---\n")

    return ''.join(report_lines)

def main():
    # Get links from links.md
    links = find_links_in_file('links.md')

    # Include any URLs found through those links
    all_links = []
    for link in links:
        all_links.append(link)  # Add the main link
        nested_links = find_links_in_page(link)  # Retrieve nested links
        all_links.extend(nested_links)
    
    # Generate the report
    analysis_report = generate_report(all_links)

    with open('analysis.md', 'w') as report_file:
        report_file.write(analysis_report)

if __name__ == "__main_
_":
    main()
