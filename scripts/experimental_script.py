import json
import os
import re
import requests
from transformers import pipeline
import warnings
import torch

# Suppress warnings and logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
warnings.filterwarnings('ignore')

class ProductSearchAssistant:
    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize models with explicit device mapping
        self.summarizer = pipeline(
            "summarization", 
            model="facebook/bart-large-cnn",
            device=0 if torch.cuda.is_available() else -1
        )
        
        self.query_parser = pipeline(
            "text2text-generation",
            model="google/flan-t5-base",
            device=0 if torch.cuda.is_available() else -1,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        
        self.location = None

    def get_user_location(self):
        return input("Enter your delivery location (city, ZIP): ")

    def parse_query(self, query):
        prompt = f"""
        Convert this query to JSON with product_type, features (array), and price_range:
        Example 1: "Quiet vacuum under $200" → {{"product_type": "vacuum cleaner", "features": ["quiet"], "price_range": "under $200"}}
        Example 2: "32 inch 4K monitor" → {{"product_type": "monitor", "features": ["32 inch", "4K"], "price_range": ""}}
        
        Query: {query}
        JSON:
        """
        try:
            response = self.query_parser(
                prompt,
                max_length=200,
                do_sample=True,
                temperature=0.3,
                top_k=30,
                num_return_sequences=1
            )
            json_str = response[0]['generated_text'].strip()
            
            # Enhanced JSON cleaning
            json_str = re.sub(r"(?i)(true|false|null)", lambda m: m.group().lower(), json_str)
            json_str = re.sub(r"[\'‘’`]", '"', json_str)
            json_str = re.sub(r"(\w)\s*:\s*", r'"\1": ', json_str)
            match = re.search(r"\{.*?\}", json_str, re.DOTALL)
            
            if not match:
                raise ValueError("No JSON found")
                
            parsed = json.loads(match.group())
            return {
                "product_type": parsed.get("product_type", query),
                "features": parsed.get("features", []),
                "price_range": parsed.get("price_range", "")
            }
        except Exception as e:
            print(f"\n⚠️ Using enhanced search for: '{query}'")
            return self._fallback_parse(query)

    def _fallback_parse(self, query):
        price_match = re.search(r"(under|less than|up to)\s*(\$\d+)", query)
        features = []
        
        keywords = {
            'quiet': ['quiet', 'silent', 'low noise'],
            'size': ['inch', 'cm', 'mm', r'\d+"'],
            'resolution': ['4K', '1080p', 'HD', 'UHD']
        }
        
        for kw, patterns in keywords.items():
            if any(re.search(p, query, re.I) for p in patterns):
                features.append(kw)
        
        return {
            "product_type": re.sub(r"(under|less than|up to)\s*\$\d+", "", query).strip(),
            "features": features,
            "price_range": price_match.group(0) if price_match else ""
        }

    def scrape_products(self, product_info):
        country_code = "de" if any(x in self.location.lower() for x in ["de", "germany", "berlin"]) else "us"
        
        search_terms = [
            product_info['product_type'],
            *[f'"{feat}"' for feat in product_info['features']],
            product_info['price_range']
        ]
        query = " ".join(filter(None, search_terms))
        
        headers = {'X-API-KEY': self.serper_api_key, 'Content-Type': 'application/json'}
        payload = json.dumps({
            "q": query,
            "gl": country_code,
            "hl": "de" if country_code == "de" else "en",
            "num": 5
        })

        try:
            response = requests.post(
                "https://google.serper.dev/shopping",
                headers=headers,
                data=payload,
                timeout=15
            )
            results = response.json().get('shopping', [])
            return [p for p in results[:5] if any(x in p.get('delivery', '').lower() for x in ['de', 'germany', 'europe'])]
        except Exception as e:
            print(f"\n🔴 Search error: {str(e)}")
            return []

    def summarize_reviews(self, reviews):
        if not reviews:
            return "No reviews available"
        
        combined = " ".join([r.get('snippet', '') for r in reviews[:3]])
        return self.summarizer(
            combined, 
            max_length=60, 
            min_length=20, 
            do_sample=False,
            truncation=True
        )[0]['summary_text']

    def find_cheapest(self, products):
        try:
            return min(
                (p for p in products if p.get('price')),
                key=lambda x: float(
                    re.search(r"[\d\.]+", x['price'].replace(',', '')).group()
                )
            )
        except:
            return None

    def run(self):
        print("🌟 Product Search Assistant 🌟")
        query = input("\nDescribe your desired product (e.g., 'Quiet vacuum under $200'): ")
        self.location = self.get_user_location()

        product_info = self.parse_query(query)
        print("\n🔍 Searching for:", product_info)

        products = self.scrape_products(product_info)
        if not products:
            print("\n❌ No products found")
            return

        for product in products:
            product['review_summary'] = self.summarize_reviews(product.get('reviews', []))

        cheapest = self.find_cheapest(products)
        
        if cheapest:
            print("\n✅ Best Match Found:")
            print(f"📛 Name: {cheapest.get('title', 'N/A')}")
            print(f"💵 Price: {cheapest.get('price', 'N/A')}")
            print(f"📦 Delivery: {cheapest.get('delivery', 'Check website')}")
            print(f"📝 Reviews: {cheapest['review_summary']}")
            print(f"🔗 Link: {cheapest.get('link', 'N/A')}")
        else:
            print("\n❌ No valid pricing information found")

        print("\n🎉 Search complete!")

if __name__ == "__main__":
    assistant = ProductSearchAssistant()
    assistant.run()