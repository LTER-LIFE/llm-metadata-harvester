import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET

import asyncio
try:
    from playwright.async_api import async_playwright
except ImportError:
    raise ImportError("""
        Playwright is not installed. Please follow the
        installation instructions at
        https://playwright.dev/python/docs/intro to install it.""")



def readWebContent(url: str) -> BeautifulSoup:
    """
    Reads the content of a webpage and returns a BeautifulSoup object.
    Param: url(str): The URL of the webpage to read.
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
    Downloads metadata XML from data portal and parses it.

    Parameters
    ----------
    url : str
        The URL of the XML to download.
    
    Returns
    -------
    xml_str : str
        The raw XML text retrieved from the URL.
    root : xml.etree.ElementTree.Element
        The parsed ElementTree root of the XML.
    
    Raises
    ------
    requests.RequestException
        If there is an issue with the HTTP request.
    xml.etree.ElementTree.ParseError
        If the XML cannot be parsed.
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

    Parameters
    ----------
    url : str
        The URL of the webpage to extract text from.

    Returns
    -------
    str
        The full visible text content extracted from the web page.

    Raises
    ------
    ImportError
        If Playwright is not installed.

    Examples
    --------
    >>> await extract_full_page_text("https://example.com")
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until='networkidle')

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

        full_text = await page.inner_text("body")
        await browser.close()

        return full_text