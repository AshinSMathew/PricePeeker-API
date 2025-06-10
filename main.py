from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import random
import time
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

HEADERS_LIST = [
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
    {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'},
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

def safe_request(url, max_retries=3):
    for _ in range(max_retries):
        try:
            headers = random.choice(HEADERS_LIST)
            response = requests.get(url, headers=headers)
            if response.status_code == 429:
                time.sleep(random.uniform(1, 5))
                continue
            return response
        except Exception as e:
            print(f"Error: {e}")
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
        amazon_url = f"https://www.amazon.in/s?k={product_name.replace(' ', '+')}"
        amazon_res = safe_request(amazon_url)
        
        if not amazon_res:
            response_data["error"] = "Failed to fetch Amazon search results"
            return response_data
            
        soup_amazon = BeautifulSoup(amazon_res.text, 'html.parser')
        amazon_link = soup_amazon.select_one('a.a-link-normal.s-no-outline[href*="/dp/"]')
        
        if amazon_link:
            amazon_product_url = "https://www.amazon.in" + amazon_link['href'].split('?')[0]
            response_data["amazon_url"] = amazon_product_url
            
            # Get Amazon price
            amazon_res = safe_request(amazon_product_url)
            if amazon_res:
                soup_amazon = BeautifulSoup(amazon_res.text, 'html.parser')
                amazon_price_el = soup_amazon.select_one('span.a-price-whole')
                if amazon_price_el:
                    response_data["amazon_price"] = price_to_int(amazon_price_el.text)
        
        # Flipkart Search & Extract URL
        flipkart_url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '%20')}"
        flipkart_res = safe_request(flipkart_url)
        
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
                flipkart_res = safe_request(flipkart_product_url)
                if flipkart_res:
                    soup_flipkart = BeautifulSoup(flipkart_res.text, 'html.parser')
                    flipkart_price_el = soup_flipkart.select_one('div._30jeq3._16Jk6d')  # Updated selector
                    if not flipkart_price_el:
                        flipkart_price_el = soup_flipkart.select_one('div.Nx9bqj.CxhGGd')
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