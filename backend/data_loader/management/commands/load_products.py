# data_loader/management/commands/load_products.py

from django.core.management.base import BaseCommand
from products.models import Product
import mongoengine
import json


class Command(BaseCommand):
    help = 'Loads initial product data into the database'

    def handle(self, *args, **options):
        # Establish the MongoDB connection
        mongoengine.connect('website', host='mongodb+srv://gptfleet:GyUeIj6ohuDZhnVi@website.ora74qp.mongodb.net/', authSource='admin', retryWrites=True, w='majority')

        product_list = [
          {
            "product_name": "Twiin Blend",
            "category": "Beard Balm",
            "description": "With coffee for relaxation, Palo Santo for stress and vetiver for depression we've combined these essential oils to give our fellow man a sharper edge on life.",
            "price": 16.00,
            "ingredients": ["Coffee", "Palo Santo", "Vetiver", "Natural butters and oils"],
            "benefits": ["Stress relief", "Mental sharpness", "Beard & skin nourishment"],
            "scent_profile": "Earthy, grounding",
            "tags": ["veteran-owned", "natural", "beard balm", "stress relief"]
          },
          {
            "product_name": "Fresh Air",
            "category": "Beard Balm",
            "description": "Having a tough day with sinuses? With peppermint, eucalyptus and rosemary we've constructed this minty scent to help with just that. We've also added lemon to help boost your mood and mental clarity.",
            "price": 16.00,
            "ingredients": ["Peppermint", "Eucalyptus", "Rosemary", "Lemon", "Natural butters and oils"],
            "benefits": ["Sinus relief", "Mood boost", "Mental clarity"],
            "scent_profile": "Minty, fresh",
            "tags": ["beard balm", "sinus", "mental clarity", "veteran-owned"]
          },
          {
            "product_name": "El Rey",
            "category": "Beard Balm",
            "description": "We are kings and we should feel and smell like one. Bourbon sandalwood and a hint of black pepper smells great and will also make your queen be proud to call you, her king.",
            "price": 16.00,
            "ingredients": ["Bourbon Sandalwood", "Black Pepper", "Natural butters and oils"],
            "benefits": ["Confidence", "Attractive aroma", "Healthy skin and beard"],
            "scent_profile": "Warm, woody, spicy",
            "tags": ["king", "sandalwood", "luxury", "beard care"]
          },
          {
            "product_name": "Union Blend",
            "category": "Beard Balm",
            "description": "Teakwood and patchouli essential oils with benefits for headaches, skin irritation, and stress. A rugged, manly scent made for Union Brothers.",
            "price": 16.00,
            "ingredients": ["Teakwood", "Patchouli", "Natural butters and oils"],
            "benefits": ["Headache relief", "Skin health", "Stress reduction"],
            "scent_profile": "Earthy, masculine",
            "tags": ["union", "patchouli", "beard balm", "rugged"]
          },
          {
            "product_name": "Valhalla Blend",
            "category": "Beard Balm",
            "description": "This energy boost has a citrusy blend for its warriors. With sweet orange, pink grapefruit and lemon it will have your soul feeling like you've entered the great halls of Valhalla.",
            "price": 16.00,
            "ingredients": ["Sweet Orange", "Pink Grapefruit", "Lemon", "Natural butters and oils"],
            "benefits": ["Energy boost", "Mood enhancement", "Beard conditioning"],
            "scent_profile": "Citrusy, vibrant",
            "tags": ["energy", "citrus", "viking", "veteran-owned"]
          },
          {
            "product_name": "Veteran Blend",
            "category": "Beard Balm",
            "description": "A tribute to fellow soldiers. With frankincense serrata, tea tree and tangerine, it honors those who can finally grow a beard now.",
            "price": 16.00,
            "ingredients": ["Frankincense Serrata", "Tea Tree", "Tangerine", "Natural butters and oils"],
            "benefits": ["Skin cleansing", "Tribute scent", "Refreshing feel"],
            "scent_profile": "Herbal, clean",
            "tags": ["veteran", "frankincense", "tea tree", "beard care"]
          },
          {
            "product_name": "Unscented Blend",
            "category": "Beard Oil",
            "description": "This blend is for those who want all the benefits of our oils without any added essential or fragrance oils.",
            "price": 13.00,
            "ingredients": ["Carrier oils (unspecified)"],
            "benefits": ["Hydration", "Skin nourishment", "Scent-free grooming"],
            "scent_profile": "None",
            "tags": ["unscented", "sensitive skin", "oil only", "minimalist"]
          },
          {
            "product_name": "Niice Dreams",
            "category": "Beard Balm",
            "description": "With bergamot, lavender and ylang ylang oils, this calming blend offers an aroma that reminds you of a good night's sleep.",
            "price": 16.00,
            "ingredients": ["Bergamot", "Lavender", "Ylang Ylang", "Natural butters and oils"],
            "benefits": ["Sleep aid", "Calming effect", "Soothing aroma"],
            "scent_profile": "Floral, calming",
            "tags": ["sleep", "lavender", "calm", "beard care"]
          },
          {
            "product_name": "Beard Wash",
            "category": "Beard Wash",
            "description": "Gentle, cleansing wash for facial hair. Available in 3 varieties (unspecified scents). Promotes healthy growth and removes buildup.",
            "price": 19.00,
            "ingredients": ["Natural cleansing agents", "Essential oils (varies by type)"],
            "benefits": ["Cleans beard", "Removes oil & dirt", "Promotes growth"],
            "scent_profile": "Varies",
            "tags": ["beard wash", "cleanse", "hydration", "veteran-owned"]
          },
          {
            "product_name": "Mustache Wax",
            "category": "Mustache Wax",
            "description": "Medium hold wax made with hempseed oil and beeswax. Keeps your mustache styled and out of your mouth.",
            "price": 13.00,
            "ingredients": ["Hempseed Oil", "Beeswax"],
            "benefits": ["Hold", "Control", "Style"],
            "scent_profile": "Natural",
            "tags": ["mustache", "wax", "style", "medium hold"]
          },
          {
            "product_name": "Tattoo Balm",
            "category": "Tattoo Balm",
            "description": "Natural balm designed to moisturize and protect tattoos. Promotes healing and vibrancy.",
            "price": 13.00,
            "ingredients": ["Natural oils", "Butters (unspecified)"],
            "benefits": ["Moisturizes", "Enhances tattoo appearance", "Promotes healing"],
            "scent_profile": "Natural or light scent",
            "tags": ["tattoo", "healing", "balm", "veteran-owned"]
          }
        ]

        for product_data in product_list:
            # Assuming your Product model fields match the keys in the dictionary
            # Add default or handle missing fields as needed
            product = Product(
                product_name=product_data.get('product_name'),
                category=product_data.get('category'),
                description=product_data.get('description'),
                price=product_data.get('price'),
                ingredients=product_data.get('ingredients', []), # Assuming ingredients is a list
                benefits=product_data.get('benefits', []),     # Assuming benefits is a list
                scent_profile=product_data.get('scent_profile'),
                variants=product_data.get('variants', []),     # Assuming variants is a list, default to empty
                tags=product_data.get('tags', []),             # Assuming tags is a list, default to empty
                availability=product_data.get('availability', True) # Assuming availability is boolean, default to True
            )
            try:
                product.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully loaded product: {product.product_name}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error loading product {product_data.get("product_name")}: {e}'))