# Price Comparator API - Amazon & Flipkart

This FastAPI-based project compares product prices between **Amazon** and **Flipkart** using a Scraper API.

It provides a single endpoint:  
`GET /compare/{product_name}`  
where `{product_name}` should be passed with `+` instead of spaces (e.g., `iphone+15+pro`).

---

## Features

- Compare product prices from Amazon and Flipkart
- Uses a third-party **Scraper API** to bypass bot protection
- Built with **Python 3** and **FastAPI**
- Returns product title, price, and URL from both sites

## Environment Variables

Create a `.env` file in the root directory and add your Scraper API key:

`SCRAPER_API_KEY=your_scraper_api_key_here`