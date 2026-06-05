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
                # Find all hyperlinks in the HTML
                for link in soup.find_all('a', href=True):
                    full_url = link['href']
                    if full_url.startswith(('http://', 'https://')):
                        links.append(full_url)
    except Exception as e:
        print(f"Error accessing {url}: {e}")
    return links

def find_links_in_repo(repo_path):
    links = []
    for root, _, files in os.walk(repo_path):
        for file_name in files:
            if file_name.endswith(('.md', '.txt')):  # Check text-based files
                with open(os.path.join(root, file_name), 'r') as file:
                    content = file.read()
                    found_links = re.findall(r'(https?://[^\s]+)', content)
                    links.extend(found_links)
                    for link in found_links:
                        nested_links = find_links_in_page(link)
                        links.extend(nested_links)
    return list(set(links))  # Remove duplicates

def analyze_media(file_url):
    try:
        response = requests.get(file_url)
        file_path = file_url.split('/')[-1]

        # Save the file locally for analysis
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
    report_lines = ["# Analysis Report\n"]
    
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

def main(repo_path):
    links = find_links_in_repo(repo_path)
    analysis_report = generate_report(links)

    with open('analysis.md', 'w') as report_file:
        report_file.write(analysis_report)

if __name__ == "__main__":
    MAIN_REPO_PATH = '.'  # Use the current directory as the repo path
    main(MA
         IN_REPO_PATH)
