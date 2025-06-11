from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import random
import time
import os
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
SCRAPER_API_URL = "http://api.scraperapi.com"

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

def scrape_with_scraperapi(url, max_retries=3):
    """
    Make requests through ScraperAPI with retry logic
    """
    params = {
        'api_key': SCRAPER_API_KEY,
        'url': url,
        'render': 'false',
        'country_code': 'in',
    }
    
    for _ in range(max_retries):
        try:
            response = requests.get(SCRAPER_API_URL, params=params, timeout=30)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                time.sleep(random.uniform(1, 3))
                continue
        except Exception as e:
            print(f"ScraperAPI error: {e}")
            time.sleep(2)
    
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
        # Amazon Search & Extract URL
        amazon_search_url = f"https://www.amazon.in/s?k={product_name.replace(' ', '+')}"
        amazon_res = scrape_with_scraperapi(amazon_search_url)
        
        if not amazon_res:
            response_data["error"] = "Failed to fetch Amazon search results"
            return response_data
            
        soup_amazon = BeautifulSoup(amazon_res.text, 'html.parser')
        amazon_link = soup_amazon.select_one('a.a-link-normal.s-no-outline[href*="/dp/"]')
        
        if amazon_link:
            amazon_product_url = "https://www.amazon.in" + amazon_link['href'].split('?')[0]
            response_data["amazon_url"] = amazon_product_url
            
            # Get Amazon price
            amazon_res = scrape_with_scraperapi(amazon_product_url)
            if amazon_res:
                soup_amazon = BeautifulSoup(amazon_res.text, 'html.parser')
                amazon_price_el = soup_amazon.select_one('span.a-price-whole')
                if amazon_price_el:
                    response_data["amazon_price"] = price_to_int(amazon_price_el.text)
        
        # Flipkart Search & Extract URL
        flipkart_search_url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '%20')}"
        flipkart_res = scrape_with_scraperapi(flipkart_search_url)
        
        if not flipkart_res:
            response_data["error"] = "Failed to fetch Flipkart search results"
            return response_data
            
        soup_flipkart = BeautifulSoup(flipkart_res.text, 'html.parser')
        flipkart_selectors = ['a.CGtC98', 'a.wjcEIp']
        flipkart_link = None
        
        for selector in flipkart_selectors:
            flipkart_link = soup_flipkart.select_one(f'{selector}[href*="/p/"]')
            if flipkart_link:
                flipkart_product_url = "https://www.flipkart.com" + flipkart_link['href']
                response_data["flipkart_url"] = flipkart_product_url
                
                # Get Flipkart price
                flipkart_res = scrape_with_scraperapi(flipkart_product_url)
                if flipkart_res:
                    soup_flipkart = BeautifulSoup(flipkart_res.text, 'html.parser')
                    price_selectors ='div.Nx9bqj.CxhGGd'
                    flipkart_price_el = soup_flipkart.select_one(price_selectors)
                    if flipkart_price_el:
                        response_data["flipkart_price"] = price_to_int(flipkart_price_el.text)
                break
        
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
    return {"message": "Welcome to the Price Comparison API. Use /compare/{product_name} to compare prices."}