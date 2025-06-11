from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import random
import time
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import Optional
import asyncio
import aiohttp
from urllib.parse import urlencode

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced headers with more variety and realistic browser fingerprints
HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    },
    {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
]

class ProductResponse(BaseModel):
    product_name: str
    amazon_url: Optional[str] = None
    flipkart_url: Optional[str] = None
    amazon_price: Optional[int] = None
    flipkart_price: Optional[int] = None
    cheaper_platform: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

def price_to_int(price_str):
    if not price_str:
        return None
    cleaned = ''.join(c for c in price_str if c.isdigit() or c == ',')
    return int(cleaned.replace(',', '')) if cleaned else None

def get_session():
    """Create a session with random delays and realistic behavior"""
    session = requests.Session()
    headers = random.choice(HEADERS_LIST)
    session.headers.update(headers)
    
    # Add some session-level configurations
    session.max_redirects = 5
    return session

async def safe_request_async(url, max_retries=3, delay_range=(2, 8)):
    """Async version with better error handling and delays"""
    for attempt in range(max_retries):
        try:
            # Random delay between requests
            if attempt > 0:
                await asyncio.sleep(random.uniform(*delay_range))
            
            headers = random.choice(HEADERS_LIST)
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers=headers
            ) as session:
                async with session.get(url) as response:
                    if response.status == 429:
                        print(f"Rate limited on attempt {attempt + 1}")
                        await asyncio.sleep(random.uniform(5, 15))
                        continue
                    elif response.status == 403:
                        print(f"Forbidden on attempt {attempt + 1}")
                        await asyncio.sleep(random.uniform(3, 10))
                        continue
                    
                    print(f"Response Status: {response.status} for {url[:50]}...")
                    text = await response.text()
                    
                    # Create a mock response object for compatibility
                    class MockResponse:
                        def __init__(self, status_code, text):
                            self.status_code = status_code
                            self.text = text
                    
                    return MockResponse(response.status, text)
                    
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(2, 5))
            continue
    
    return None

def safe_request(url, max_retries=3, delay_range=(2, 8)):
    """Enhanced synchronous version with better anti-detection"""
    session = get_session()
    
    for attempt in range(max_retries):
        try:
            # Random delay between requests
            if attempt > 0:
                time.sleep(random.uniform(*delay_range))
            
            # Rotate headers for each attempt
            headers = random.choice(HEADERS_LIST)
            session.headers.update(headers)
            
            response = session.get(
                url, 
                timeout=30,
                allow_redirects=True,
                verify=True
            )
            
            if response.status_code == 429:
                print(f"Rate limited on attempt {attempt + 1}")
                time.sleep(random.uniform(5, 15))
                continue
            elif response.status_code == 403:
                print(f"Forbidden on attempt {attempt + 1} - trying different approach")
                time.sleep(random.uniform(3, 10))
                continue
            elif response.status_code == 503:
                print(f"Service unavailable on attempt {attempt + 1}")
                time.sleep(random.uniform(5, 12))
                continue
            
            print(f"Response Status: {response.status_code} for {url[:50]}...")
            return response
            
        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt + 1}")
            time.sleep(random.uniform(2, 5))
        except requests.exceptions.ConnectionError:
            print(f"Connection error on attempt {attempt + 1}")
            time.sleep(random.uniform(3, 8))
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(random.uniform(2, 5))
    
    session.close()
    return None

def extract_flipkart_price_with_fallbacks(soup):
    """Multiple selectors for Flipkart price extraction"""
    price_selectors = [
        'div._30jeq3._16Jk6d',
        'div.Nx9bqj.CxhGGd', 
        'div._25b18c',
        'div._30jeq3',
        'span._30jeq3._16Jk6d',
        'div.CEmiEU div._30jeq3',
        'div._3I9_wc._27UcVY',
        '[data-testid="price-mp-label"]',
        '.Nx9bqj',
        '._30jeq3'
    ]
    
    for selector in price_selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text(strip=True)
            if price_text and any(char.isdigit() for char in price_text):
                return price_to_int(price_text)
    return None

def extract_amazon_price_with_fallbacks(soup):
    """Multiple selectors for Amazon price extraction"""
    price_selectors = [
        'span.a-price-whole',
        'span.a-price.a-text-price.a-size-medium.apexPriceToPay span.a-offscreen',
        'span.a-price.a-text-price.a-size-base span.a-offscreen',
        'span#price_inside_buybox',
        'span.a-price.a-text-price.a-size-medium.apexPriceToPay',
        'span.a-price-range',
        '.a-price .a-offscreen'
    ]
    
    for selector in price_selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text(strip=True)
            if price_text and any(char.isdigit() for char in price_text):
                return price_to_int(price_text)
    return None

@app.get("/compare/{product_name}", response_model=ProductResponse)
async def compare_prices(product_name: str):
    response_data = {
        "product_name": product_name.replace('+', ' '),
        "amazon_url": None,
        "flipkart_url": None,
        "amazon_price": None,
        "flipkart_price": None,
        "cheaper_platform": None,
        "message": None,
        "error": None
    }
    
    try:
        # Add initial delay to simulate human behavior
        await asyncio.sleep(random.uniform(1, 3))
        
        # Amazon Search & Extract URL
        amazon_search_query = product_name.replace(' ', '+')
        amazon_url = f"https://www.amazon.in/s?k={amazon_search_query}&ref=sr_pg_1"
        
        print(f"Searching Amazon for: {product_name}")
        amazon_res = safe_request(amazon_url)
        
        if amazon_res and amazon_res.status_code == 200:
            soup_amazon = BeautifulSoup(amazon_res.text, 'html.parser')
            amazon_link = soup_amazon.select_one('a.a-link-normal.s-no-outline[href*="/dp/"]')
            
            if amazon_link:
                amazon_product_url = "https://www.amazon.in" + amazon_link['href'].split('?')[0]
                response_data["amazon_url"] = amazon_product_url
                
                # Add delay before fetching product page
                await asyncio.sleep(random.uniform(2, 4))
                
                # Get Amazon price
                amazon_res = safe_request(amazon_product_url)
                if amazon_res and amazon_res.status_code == 200:
                    soup_amazon = BeautifulSoup(amazon_res.text, 'html.parser')
                    response_data["amazon_price"] = extract_amazon_price_with_fallbacks(soup_amazon)
        
        # Add delay between Amazon and Flipkart requests
        await asyncio.sleep(random.uniform(3, 6))
        
        # Flipkart Search & Extract URL with enhanced approach
        flipkart_search_query = product_name.replace(' ', '%20')
        flipkart_url = f"https://www.flipkart.com/search?q={flipkart_search_query}&sort=relevance"
        
        print(f"Searching Flipkart for: {product_name}")
        flipkart_res = safe_request(flipkart_url, delay_range=(3, 8))
        
        if flipkart_res and flipkart_res.status_code == 200:
            soup_flipkart = BeautifulSoup(flipkart_res.text, 'html.parser')
            
            # Enhanced Flipkart link selectors
            flipkart_selectors = [
                'a.CGtC98[href*="/p/"]',
                'a.wjcEIp[href*="/p/"]',
                'a._2rpwqI[href*="/p/"]',
                'a.IRpwTa[href*="/p/"]',
                'a[href*="/p/"]'
            ]
            
            flipkart_link = None
            for selector in flipkart_selectors:
                flipkart_link = soup_flipkart.select_one(selector)
                if flipkart_link:
                    break
            
            if flipkart_link:
                flipkart_href = flipkart_link['href']
                if not flipkart_href.startswith('http'):
                    flipkart_product_url = "https://www.flipkart.com" + flipkart_href
                else:
                    flipkart_product_url = flipkart_href
                    
                response_data["flipkart_url"] = flipkart_product_url
                
                # Add longer delay before fetching Flipkart product page
                await asyncio.sleep(random.uniform(4, 8))
                
                # Get Flipkart price
                flipkart_res = safe_request(flipkart_product_url, delay_range=(4, 10))
                if flipkart_res and flipkart_res.status_code == 200:
                    soup_flipkart = BeautifulSoup(flipkart_res.text, 'html.parser')
                    response_data["flipkart_price"] = extract_flipkart_price_with_fallbacks(soup_flipkart)
        
        # Compare prices
        if response_data["amazon_price"] is not None and response_data["flipkart_price"] is not None:
            if response_data["amazon_price"] < response_data["flipkart_price"]:
                response_data["cheaper_platform"] = "Amazon"
            elif response_data["amazon_price"] > response_data["flipkart_price"]:
                response_data["cheaper_platform"] = "Flipkart"
            else:
                response_data["cheaper_platform"] = "Both have same price"
        elif response_data["amazon_price"] is not None:
            response_data["message"] = "Only Amazon price available"
        elif response_data["flipkart_price"] is not None:
            response_data["message"] = "Only Flipkart price available"
        else:
            response_data["message"] = "No prices found"
        
        return response_data
    
    except Exception as e:
        response_data["error"] = f"An error occurred: {str(e)}"
        return response_data

@app.get("/")
async def root():
    return {"message": "Welcome to the Enhanced Price Comparison API. Use /compare/{product_name} to compare prices."}