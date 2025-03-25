import os
from urllib.parse import urlparse
from flask import request, Response, stream_with_context, Flask
from markupsafe import escape

from openai import OpenAI
from serpapi import GoogleSearch
import functions_framework
from flask_cors import cross_origin 
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Retrieve your API keys from environment variables
OPENAI_KEY = os.environ.get("OPENAI_KEY")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")

client = OpenAI(api_key=OPENAI_KEY)

# Create Flask app
app = Flask(__name__)

def parse_location(user_location):
    """Convert user location to a SerpAPI-compatible country code."""
    country_code = "us"  # Default to US
    if "," in user_location:
        country_part = user_location.split(",")[-1].strip().lower()
        country_mapping = {
            "usa": "us", "us": "us", "uk": "gb", "united kingdom": "gb",
            "canada": "ca", "germany": "de", "france": "fr"
        }
        country_code = country_mapping.get(country_part, "us")
    return country_code

def find_product_reviews(product_title, country_code):
    """Find top review excerpts for a product."""
    params = {
        "engine": "google",
        "q": f"{product_title} reviews",
        "api_key": SERPAPI_KEY,
        "gl": country_code,
        "hl": "en",
        "num": 3  # Get top 3 review sources
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict().get("organic_results", [])
        valid_sources = ["amazon", "bestbuy", "rtings", "techradar", "wired"]
        return [
            r for r in results
            if any(src in r.get('link', '') for src in valid_sources)
        ][:3]
    except Exception as e:
        print(f"Review search error: {e}")
        return []

def summarize_reviews(review_data):
    """Analyze review excerpts using GPT-4 and return a concise summary."""
    sources_text = "\n".join(
        f"Source {i+1}: {r.get('snippet', 'No review text found')[:300]}"
        for i, r in enumerate(review_data)
    )

    prompt = f"""Analyze these product review excerpts:

{sources_text}

Create a concise summary with:
- 3 key positive aspects
- 3 common criticisms
Keep each point under 15 words. Be factual and avoid speculation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional product analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Summary error: {e}")
        return "Unable to generate summary"

def get_purchase_info(product):
    """Extract purchase information from a product dictionary."""
    if "sellers" in product:
        for seller in product["sellers"]:
            if seller.get("link"):
                return {
                    "price": seller.get("price", "N/A"),
                    "seller": seller.get("name", "Unknown Seller"),
                    "link": seller["link"]
                }
    if "link" in product:
        return {
            "price": product.get("price", "N/A"),
            "seller": "Google Shopping",
            "link": product["link"]
        }
    return {
        "price": product.get("price", "N/A"),
        "seller": "No seller available",
        "link": "https://www.google.com/search?tbm=shop&q=" + product.get("title", "").replace(" ", "+")
    }

def search_products(query, country_code):
    """Search for products using the Google Shopping API."""
    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERPAPI_KEY,
        "gl": country_code,
        "hl": "en",
        "num": 10  # Get more results to find ones with links
    }
    try:
        search = GoogleSearch(params)
        response = search.get_dict()
        results = response.get("shopping_results", [])
        # Prioritize products that have purchase links (sellers)
        return sorted(
            results,
            key=lambda x: 0 if x.get("sellers") else 1
        )[:5]
    except Exception as e:
        print(f"Product search error: {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
@cross_origin()
def product_search():
    """
    HTTP endpoint that accepts a product query and streams
    output gradually as it's generated. It ignores any provided location
    and always uses 'Berlin, Germany'.
    """
    # Support GET and POST methods.
    if request.method == 'GET':
        query = request.args.get('query')
    elif request.method == 'POST':
        query = request.form.get('query')
    else:
        return Response("Method not allowed", status=405)

    if not query:
        return Response("Missing 'query' parameter", status=400)

    # Sanitize the query.
    query = escape(query)
    
    # Hardcoded location.
    location = "Berlin, Germany"
    country_code = parse_location(location)

    def generate_response():
        products = search_products(query, country_code)
        if not products:
            yield "No products found.\n"
            return
        for idx, product in enumerate(products, 1):
            title = product.get('title', 'No title available')
            yield f"Product {idx}: {title}\n"
            purchase_info = get_purchase_info(product)
            yield f"  Price: {purchase_info['price']}\n"
            yield f"  Purchase Link: {purchase_info['link']}\n"
            yield "  Analyzing reviews...\n"
            reviews = find_product_reviews(title, country_code)
            if reviews:
                summary = summarize_reviews(reviews)
                yield "  Review Summary:\n"
                yield f"    {summary}\n"
                yield "  Review Sources:\n"
                for r in reviews:
                    domain = urlparse(r.get("link", "")).netloc.replace("www.", "")
                    yield f"    {domain}: {r.get('link', '')}\n"
            else:
                yield "  No reviews found from trusted sources.\n"
            yield "\n"
    
    return Response(stream_with_context(generate_response()), mimetype='text/plain')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)