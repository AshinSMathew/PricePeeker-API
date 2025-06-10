from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Allow CORS for all origins (you might want to restrict this in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

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
        amazon_res = requests.get(amazon_url, headers=headers)
        amazon_res.raise_for_status()
        
        soup_amazon = BeautifulSoup(amazon_res.text, 'html.parser')
        amazon_link = soup_amazon.select_one('a.a-link-normal.s-no-outline[href*="/dp/"]')
        
        if amazon_link:
            amazon_product_url = "https://www.amazon.in" + amazon_link['href'].split('?')[0]
            response_data["amazon_url"] = amazon_product_url
            
            # Get Amazon price
            amazon_res = requests.get(amazon_product_url, headers=headers)
            amazon_res.raise_for_status()
            soup_amazon = BeautifulSoup(amazon_res.text, 'html.parser')
            amazon_price_el = soup_amazon.select_one('span.a-price-whole')
            if amazon_price_el:
                response_data["amazon_price"] = price_to_int(amazon_price_el.text)
        
        # Flipkart Search & Extract URL
        flipkart_url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '%20')}"
        flipkart_res = requests.get(flipkart_url, headers=headers)
        flipkart_res.raise_for_status()
        
        soup_flipkart = BeautifulSoup(flipkart_res.text, 'html.parser')
        flipkart_selectors = ['a.CGtC98', 'a.wjcEIp']
        flipkart_link = None
        
        for selector in flipkart_selectors:
            flipkart_link = soup_flipkart.select_one(f'{selector}[href*="/p/"]')
            if flipkart_link:
                flipkart_product_url = "https://www.flipkart.com" + flipkart_link['href']
                response_data["flipkart_url"] = flipkart_product_url
                
                # Get Flipkart price
                flipkart_res = requests.get(flipkart_product_url, headers=headers)
                flipkart_res.raise_for_status()
                soup_flipkart = BeautifulSoup(flipkart_res.text, 'html.parser')
                flipkart_price_el = soup_flipkart.select_one('div.Nx9bqj.CxhGGd')
                if flipkart_price_el:
                    response_data["flipkart_price"] = price_to_int(flipkart_price_el.text)
                break
        
        # Compare prices
        if response_data["amazon_price"] and response_data["flipkart_price"]:
            if response_data["amazon_price"] < response_data["flipkart_price"]:
                response_data["cheaper_platform"] = "Amazon"
            elif response_data["amazon_price"] > response_data["flipkart_price"]:
                response_data["cheaper_platform"] = "Flipkart"
            else:
                response_data["cheaper_platform"] = "Both have same price"
        elif response_data["amazon_price"]:
            response_data["message"] = "Only Amazon price available"
        elif response_data["flipkart_price"]:
            response_data["message"] = "Only Flipkart price available"
        else:
            response_data["message"] = "No prices found"
        
        return response_data
    
    except requests.exceptions.RequestException as e:
        response_data["error"] = f"Request error: {str(e)}"
        return response_data
    except Exception as e:
        response_data["error"] = f"An error occurred: {str(e)}"
        return response_data

@app.get("/")
async def root():
    return {"message": "Welcome to the Price Comparison API. Use /compare/{product_name} to compare prices."}