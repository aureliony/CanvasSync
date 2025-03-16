"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

url_utilities.py, module

A collection of functions that creates URL shortcuts and downloads them.
"""

import mimetypes
import os
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import urlparse

import requests

from CanvasSync.utilities.helpers import get_corrected_name

# List of domains that we should not download
BLACKLISTED_DOMAINS = [
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "dailymotion.com",
    "twitch.tv",
    "ap.panopto.com"
]


def _make_mac_url_shortcut(url: str, path: str):
    url_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
<key>URL</key>
<string>%s</string>
</dict>
</plist>""" % url
    filepath = path + ".webloc"
    return url_content.encode("utf-8"), filepath


def _make_linux_url_shortcut(url: str, path: str):
    name = os.path.split(url)[-1]
    url_content = """[Desktop Entry]
Encoding=UTF-8
Name=%s
Type=Link
URL=%s
Icon=text-html""" % (name, url)
    filepath = path + ".desktop"
    return url_content.encode("utf-8"), filepath


def _make_windows_url_shortcut(url: str, path: str):
    url_content = """[InternetShortcut]
URL=%s""" % url
    filepath = path + ".url"
    return url_content.encode("utf-8"), filepath


def make_url_shortcut(url, path):
    system = sys.platform.lower()

    if system == "darwin":
        new_content, filepath = _make_mac_url_shortcut(url, path)
    elif "linux" in system:
        new_content, filepath = _make_linux_url_shortcut(url, path)
    else:
        new_content, filepath = _make_windows_url_shortcut(url, path)

    if os.path.exists(filepath):
        old_content = open(filepath, "rb").read()
        if new_content == old_content:
            return False

    open(filepath, "wb").write(new_content)
    return True


def url_is_blacklisted(url: str) -> bool:
    """Returns True if the URL is blacklisted, otherwise False."""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()  # Extract domain & make it lowercase

        # Check if domain (or subdomain) belongs to a blacklisted site
        return any(domain.endswith(blacklisted_domain) for blacklisted_domain in BLACKLISTED_DOMAINS)

    except Exception as e:
        return False


def get_last_modified(response: requests.Response) -> Optional[datetime]:
    last_modified_time = response.headers.get('Last-Modified')
    if last_modified_time:
        return parsedate_to_datetime(last_modified_time)

    return None


def download_url_content(url: str, path: str) -> bool:
    """
    Downloads the content from the given URL and saves it to the specified path 
    only if the remote file is newer than the local one.
    """
    
    if url_is_blacklisted(url):
        return False

    # Extract filename from the URL or fallback to the provided path
    mime_type, _ = mimetypes.guess_type(url)
    actual_ext = mimetypes.guess_extension(mime_type) if mime_type else None
    _, expected_ext = os.path.splitext(url)
    if expected_ext is not None and expected_ext == actual_ext:
        filename = os.path.basename(url)
    else:
        filename = os.path.basename(path) + (actual_ext or ".html")
    filepath = os.path.join(os.path.dirname(path), get_corrected_name(filename))

    # Check for last modified
    if os.path.exists(filepath):
        try:
            head_response = requests.head(url)

        except Exception:
            return False

        remote_last_modified = get_last_modified(head_response)
        if remote_last_modified:
            local_modified_time = datetime.fromtimestamp(os.path.getmtime(filepath), timezone.utc)
            # print(remote_last_modified)
            # print(local_modified_time)
            if remote_last_modified <= local_modified_time:
                return False

    try:
        # Download the file if it's new or doesn't exist
        response = requests.get(url)
        response.raise_for_status()

    except Exception:
        return False

    if os.path.exists(filepath):
        old_file_data = open(filepath, "rb").read()
        file_was_changed = old_file_data != response.content
        new_file_size_ratio = len(response.content) / max(1, len(old_file_data)) # avoid zero division
        # If the new file size is less than half of the old file size, it has likely been removed
        if file_was_changed and new_file_size_ratio > 0.5:
            open(filepath, "wb").write(response.content)

    else:
        open(filepath, "wb").write(response.content)

    remote_last_modified = get_last_modified(response)
    if remote_last_modified:
        modtime = remote_last_modified.timestamp()
        os.utime(filepath, times=(modtime, modtime))

    return file_was_changed
