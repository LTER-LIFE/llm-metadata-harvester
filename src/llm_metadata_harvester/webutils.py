import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET

import asyncio


def readWebContent(url: str) -> BeautifulSoup:
    """
    Reads the content of a webpage and returns a BeautifulSoup object.
    :param url: The URL of the webpage to read.
    :return: A BeautifulSoup object containing the parsed HTML content.
    """
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    else:
        print("Failed to retrieve the webpage.")
        return None

def downloadAndParseXML(url):
    """
    Downloads metadata XML from the Wadden data service and parses it.
    Params: url (str): The URL of the XML to download.
    Returns: tuple: (xml_str, root) where xml_str is the raw XML text and root is the parsed ElementTree root
    """

    # Download the XML
    response = requests.get(url)
    xml_str = response.text
    
    # Parse the XML
    root = ET.fromstring(xml_str)
    
    return xml_str, root

async def extract_full_page_text(url: str) -> str:
    """
    Asynchronously extracts all visible text content from a web page.

    This function uses Playwright to launch a headless Chromium browser, navigate
    to the specified URL, scrolls to the bottom of the page to ensure lazy-loaded
    content is displayed, and then retrieves all inner text from the page's body.

    :param url: The URL of the webpage to read.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until='networkidle')

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

        full_text = await page.inner_text("body")
        await browser.close()

        return full_text