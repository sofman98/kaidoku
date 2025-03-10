import os
from dotenv import load_dotenv
from scrapegraphai.graphs import SearchGraph, SmartScraperMultiGraph
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Optional
from collections import defaultdict
import json
import re

# Load environment variables
load_dotenv()

class ProductSchema(BaseModel):
    name: str = Field(description="Official product name")
    description: str = Field(description="Key product features and specifications")
    price: float = Field(description="Current price in local currency")
    pros: List[str] = Field(description="List of positive aspects from customer reviews")
    cons: List[str] = Field(description="List of negative aspects from customer reviews")
    rating: float = Field(description="Average user rating (0-5 scale)")
    retailer: str = Field(description="E-commerce platform name")
    product_url: str = Field(description="Direct purchase link")
    delivery_available: bool = Field(description="Availability in user's location")

class ProductSearchAssistant:
    def __init__(self):
        # Ollama configuration
        self.search_config = {
            "llm": {
                "model": "ollama/llama3",
                "base_url": "http://localhost:11434",
                "temperature": 0.3
            },
            "max_results": 10,
            "verbose": True
        }
        
        self.scrape_config = {
            "llm": {
                "model": "ollama/llama3",
                "base_url": "http://localhost:11434",
            },
            "headless": True
        }

    def process_query(self, user_query: str, location: str = "US") -> List[ProductSchema]:
        """Main workflow using Ollama"""
        # Step 1: Convert natural language to structured search
        search_graph = SearchGraph(
            prompt=f"Convert this product request to optimal search queries: '{user_query}'",
            config=self.search_config
        )
        search_terms = search_graph.run()
        
        # Step 2: Find products using search engine
        product_search = SearchGraph(
            prompt=f"Find {user_query} available in {location} with reviews and prices",
            config={**self.search_config, "max_results": 15}
        )
        product_links = product_search.run()
        
        # Step 3: Scrape product details with review analysis
        scraper = SmartScraperMultiGraph(
            prompt=f"""Extract and analyze product details for items available in {location}:
            1. Product name and technical specifications
            2. List 3-5 main pros from customer reviews
            3. List 3-5 main cons from customer reviews
            4. Current price and seller information
            5. Delivery availability to {location}""",
            sources=product_links,
            config=self.scrape_config,
            schema=ProductSchema
        )

def parse_query(self, query):
    prompt = f"""
    Extract product type, features, and price range from this query: '{query}'. 
    Your response must be a JSON object with no additional text. Example:

    {{
        "product_type": "vacuum cleaner",
        "features": ["quiet", "cheap"],
        "price_range": ""
    }}

    Process query: {query}
    """
    
    response = self.llm_query_parser(prompt, max_length=200, temperature=0.1)
    generated_text = response[0]['generated_text']
    
    # Extract JSON substring using regex
    json_match = re.search(r"\{.*\}", generated_text)
    json_text = json_match.group() if json_match else "{}"
    
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return {
            "product_type": "",
            "features": [],
            "price_range": ""
        }
        
        raw_results = scraper.run()
        
        # Step 4: Process results to find cheapest available options
        return self._process_results(raw_results)

    def _process_results(self, results: List[ProductSchema]) -> List[ProductSchema]:
        """Group products and find cheapest available option for each"""
        product_groups = defaultdict(list)
        
        # Group products by name and filter available ones
        for product in results:
            if product.delivery_available:
                product_groups[product.name].append(product)
        
        # Select cheapest option for each product
        final_results = []
        for name, products in product_groups.items():
            try:
                cheapest_product = min(products, key=lambda x: x.price)
                final_results.append(cheapest_product)
            except ValueError:
                continue  # Skip if no valid products
        
        # Sort by rating then price
        return sorted(final_results, key=lambda x: (-x.rating, x.price))

# Example usage
if __name__ == "__main__":
    print("""
    ===== REQUIRED SETUP =====
    1. Install Ollama: https://ollama.com/
    2. Run these commands:
    ollama serve &
    ollama pull llama3
    """)
    
    assistant = ProductSearchAssistant()
    query = "quiet vacuum cleaner under $200"
    location = "California"
    
    print(f"\nSearching for: {query} in {location}...")
    results = assistant.process_query(query, location)
    
    if not results:
        print("\nNo products found matching your criteria.")
    else:
        print(f"\nTop {len(results)} Results:")
        for idx, product in enumerate(results, 1):
            print(f"\n{idx}. {product.name}")
            print(f"   Price: ${product.price:.2f}")
            print(f"   Rating: {product.rating}/5")
            print(f"   Key Features: {product.description}")
            print(f"   Pros: {', '.join(product.pros[:3])}")
            print(f"   Cons: {', '.join(product.cons[:3])}")
            print(f"   Available at: {product.retailer}")
            print(f"   Purchase URL: {product.product_url}")