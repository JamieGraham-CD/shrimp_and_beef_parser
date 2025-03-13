from pydantic import BaseModel, Field 
from typing import List, Optional, Literal


class BeefAttributes(BaseModel):

    is_match: bool = Field(..., description="Indicates whether the user-input HTML has information about the matching user-given beef product.")
    product_name_scraped: Optional[str] = Field(..., description="Name of the beef product.")
    manufacturer: Optional[str] = Field(None, description="Name of the manufacturer or brand.")
    size: Optional[str] = Field(None, description="Size of the beef product in units of measure (e.g. 17 lbs).")
    fat_level: Optional[str] = Field(None, description="Level of fat content in the beef (e.g., lean, medium, high).")
    breed: Optional[Literal[
        "Wagyu", "Kobe", "Kauai", "Akaushi", "Hereford", "Angus"
    ]] = Field(None, description="The breed of the cattle. Options: Wagyu, Kobe, Kauai, Akaushi, Hereford, Angus.")
    temperature: Optional[Literal[
        "Fresh", "Frozen"
    ]] = Field(None, description="Storage temperature of the beef. Options: Fresh, Frozen.")
    quality: Optional[Literal[
        "No Roll", "Choice", "Prime", "Select"
    ]] = Field(None, description="Quality grading of the beef. Options: No Roll, Choice, Prime, Select.")
    type_blend: Optional[Literal[
        "Brisket/Chuck Blend", "Beef and Turkey", "Beef and Chicken", "Steakburger"
    ]] = Field(None, description="Type or blend of beef. Options: Brisket/Chuck Blend, Beef and Turkey, Beef and Chicken, Steakburger.")
    flavor: Optional[Literal[
        "Mushroom", "Teriyaki", "Jalapeno", "With Au Jus", "Mesquite", "With Onion",
        "With Peppers", "BBQ", "With Beans", "Cheese", "Seasoned"
    ]] = Field(None, description="Flavor profile or seasoning of the beef. Options: Mushroom, Teriyaki, Jalapeno, With Au Jus, Mesquite, With Onion, With Peppers, BBQ, With Beans, Cheese, Seasoned.")
    includes_soy: Optional[bool] = Field(None, description="Indicates whether the beef contains soy ingredients (True = Includes Soy).")
    is_antibiotic_free: Optional[bool] = Field(None, description="Indicates whether the beef is antibiotic-free.")
    is_grass_fed: Optional[bool] = Field(None, description="Indicates whether the beef comes from grass-fed cattle.")
    is_kosher: Optional[bool] = Field(None, description="Indicates whether the beef is certified kosher.")
    is_halal: Optional[bool] = Field(None, description="Indicates whether the beef is certified halal.")
    is_child_nutrition: Optional[bool] = Field(None, description="Indicates whether the beef meets child nutrition requirements.")
    is_low_sodium: Optional[bool] = Field(None, description="Indicates whether the beef is low in sodium.")
    shape: Optional[Literal[
        "Oval/Hoagie", "Round", "Square", "Cloud"
    ]] = Field(None, description="Physical shape of the beef product. Options: Oval/Hoagie, Round, Square, Cloud.")
    thickness: Optional[Literal[
        "3/8 inch Thick", "1/2 inch  Thick", "1 inch Thick", "5/8 inch Thick", "3/4 inch Thick", "1/8 inch Thick"
    ]] = Field(None, description="Thickness of the beef cut. Options: 3/8 inch Thick, 1/2 inch Thick, 1 inch Thick, 5/8 inch Thick, 3/4 inch Thick, 1/8 inch Thick.")
    is_gluten_free: Optional[bool] = Field(None, description="Indicates whether the beef is gluten-free.")
    opl: Optional[str] = Field(None, description="Other product labeling or special classification.")

class BeefAttributesFinalizer(BeefAttributes):
    Primary_Beef_URL: str = Field(..., description="Primary URL for beef product information.")
    Secondary_Beef_URLs: List[str] = Field(..., description="Secondary URLs for beef product information.")
    Confidence_Score_Beef: float = Field(..., description="Confidence score for the beef product.")
    Confidence_Explanation_Beef: str = Field(..., description="Explanation of the confidence score for the beef product.")

class ShrimpAttributes(BaseModel):
    
    is_match: bool = Field(..., description="Indicates whether the user-input HTML has information about the matching user-given shrimp product.")
    product_name_scraped: Optional[str] = Field(..., description="Name of the shrimp product.")
    manufacturer: Optional[str] = Field(None, description="Name of the manufacturer or brand.")
    size: Optional[str] = Field(None, description="Size of the shrimp product in units of measure (e.g. 17 lbs).")
    type: Optional[Literal[
        "Black Tiger", "Blue", "Brown", "Pink", "Prawn", "Red", "Rock", "White"
    ]] = Field(None, description="Type of shrimp. Options: Black Tiger, Blue, Brown, Pink, Prawn, Red, Rock, White.")
    head_on: Optional[bool] = Field(None, description="Indicates whether the shrimp has its head on (True = Head On).")
    shell_on: Optional[Literal[
        "EZ Peel", "Peeled", "Shell On"
    ]] = Field(None, description="Shell status of the shrimp. Options: EZ Peel, Peeled, Shell On.")
    deveined: Optional[bool] = Field(None, description="Indicates whether the shrimp is deveined (True = Deveined).")
    tail_on: Optional[bool] = Field(None, description="Indicates whether the shrimp has its tail on (False = Tail Off).")
    size_range: Optional[Literal[
        "10 ct - 15.9 ct", "100 ct - 199.9 ct", "16 ct - 20.9 ct", "200 ct and Greater",
        "21 ct - 25.9 ct", "26 ct - 30.9 ct", "31 ct - 40.9 ct", "41 ct - 60.9 ct",
        "61 ct - 99.9 ct", "9.9 ct or Fewer", "Pieces"
    ]] = Field(None, description="Shrimp size range per pound. Options: 10 ct - 15.9 ct, 100 ct - 199.9 ct, 16 ct - 20.9 ct, etc.")
    origin: Optional[Literal[
        "Domestic", "Imported"
    ]] = Field(None, description="Shrimp origin. Options: Domestic, Imported.")
    processing_doneness: Optional[Literal[
        "Cooked", "Smoked"
    ]] = Field(None, description="Processing or doneness level. Options: Cooked, Smoked.")
    butterflied: Optional[Literal[
        "Butterflied", "EBI", "Skewered"
    ]] = Field(None, description="Butterflied processing style. Options: Butterflied, EBI, Skewered.")
    wild_farmed: Optional[Literal[
        "Farmed", "Wild"
    ]] = Field(None, description="Indicates whether the shrimp is farmed or wild-caught. Options: Farmed, Wild.")
    portion_size: Optional[Literal[
        "1 lb and Under", "1.1 lbs - 2.9 lbs", "10.1 lbs - 25 lbs", "25.1 lbs and Above",
        "3 lbs - 5 lbs", "5.1 lbs - 10 lbs"
    ]] = Field(None, description="Portion size range. Options: 1 lb and Under, 1.1 lbs - 2.9 lbs, etc.")
    is_chemical_free: Optional[bool] = Field(None, description="Indicates whether the shrimp is chemical-free (True = Chemical Free).")
    opl: Optional[Literal[
        "OPL - Biaggi's", "OPL - Copelands", "OPL - Festival", "OPL - Granite City", "OPL - Hooter's",
        "OPL - Landry's", "OPL - Long John Silvers", "OPL - MGM Grand", "OPL - Oishii",
        "OPL - Panda Express", "OPL - Red Robin Restaurants", "OPL - Ruth Chris",
        "OPL - Sea Island", "OPL - Village Tavern", "OPL - Wing House", "Usda Commodities"
    ]] = Field(None, description="Other product labeling. Options: OPL - Biaggi's, OPL - Copelands, etc.")

class ShrimpAttributesFinalizer(ShrimpAttributes):
    Primary_Shrimp_URL: str = Field(..., description="Primary URL for shrimp product information.")
    Secondary_Shrimp_URLs: List[str] = Field(..., description="Secondary URLs for shrimp product information.")
    Confidence_Score_Shrimp: float = Field(..., description="Confidence score for the shrimp product.")
    Confidence_Explanation_Shrimp: str = Field(..., description="Explanation of the confidence score for the shrimp product.")




class ServingSizeValidationData(BaseModel):
    Is_Valid: bool
    Errors: List[str]


class ScrapedData(BaseModel):
    Product_Name: str
    Serving_Size: str   
    Servings_Per_Container:str
    Calories: str
    Total_Fat: str
    Saturated_Fat: str
    Trans_Fat: str
    Cholesterol: str
    Sodium: str
    Total_Carbohydrate: str
    Dietary_Fiber: str
    Total_Sugars: str
    Added_Sugars: str
    Protein: str
    Ingredients: List[str]
    
    # Allergen information
    Peanuts: Optional[str] = Field(None, description="Yes, No, undetermined, or May Contain")
    Tree_Nuts: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Soy: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Milk: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Eggs: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Wheat: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Shellfish: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    
    # Additional dietary and product attributes
    Gluten_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Lactose_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Artificial_Sweetener_Added: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Caffeine_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Sugar_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    No_Sugar_Added: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Organic: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Vegan: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Vegetarian: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Dairy_Alternative: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Kosher: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Halal: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Non_GMO: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Keto: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Cruelty_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")

    log: str


class TierData(BaseModel):
    Tier_1: List[str]
    Tier_2: List[str]

class ProductData(BaseModel):
    
    Product_Name_Scraped: str
    Serving_Size: str
    Servings_Per_Container:str
    Calories: str
    Total_Fat: str
    Saturated_Fat: str
    Trans_Fat: str
    Cholesterol: str
    Sodium: str
    Total_Carbohydrate: str
    Dietary_Fiber: str
    Total_Sugars: str
    Added_Sugars: str
    Protein: str
    Ingredients: List[str]
    
    # Allergen information
    Peanuts: Optional[str] = Field(None, description="Yes, No, undetermined, or May Contain")
    Tree_Nuts: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Soy: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Milk: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Eggs: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Wheat: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Shellfish: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    
    # Additional dietary and product attributes
    Gluten_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Lactose_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Artificial_Sweetener_Added: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Caffeine_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Sugar_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    No_Sugar_Added: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Organic: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Vegan: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Vegetarian: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Dairy_Alternative: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Kosher: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Halal: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Non_GMO: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Keto: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Cruelty_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    
    # Tier data and confidence
    Tier_1: List[str]
    Tier_2: List[str]
    Confidence_Score: float
    Confidence_Explanation: str
    log: str


class ProductIngredientsData(BaseModel):
    
    Product_Name_Scraped: str
    Serving_Size: str
    Ingredients: List[str]

    log: str

class FinalProductIngredientsData(ProductIngredientsData):
    
    Primary_Ingredients_URL: str
    Secondary_Ingredients_URL: List[str]
    Confidence_Score_Ingredients: float
    Confidence_Explanation_Ingredients: str


class ProductAllergensData(BaseModel): 
    
    Product_Name_Scraped: str
    Serving_Size: str

    # Allergen information
    Peanuts: Optional[str] = Field(None, description="Yes, No, undetermined, or May Contain")
    Mfg_In_Facility_Peanuts: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Tree_Nuts: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Mfg_In_Facility_Tree_Nuts: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Soy: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Milk: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Eggs: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Wheat: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    Shellfish: Optional[str] = Field(None, description="Yes, No, or undetermined, or May Contain")
    
    # Additional dietary and product attributes
    Gluten_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Lactose_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Artificial_Sweetener_Added: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Caffeine_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Sugar_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    No_Sugar_Added: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Organic: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Vegan: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Vegetarian: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Dairy_Alternative: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Kosher: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Halal: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Non_GMO: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Keto: Optional[str] = Field(None, description="Yes, No, or undetermined")
    Cruelty_Free: Optional[str] = Field(None, description="Yes, No, or undetermined")
    
    log: str


class FinalProductAllergensData(ProductAllergensData): 

    Primary_Allergens_URL: str
    Secondary_Allergens_URL: List[str]
    Confidence_Score_Allergens: float
    Confidence_Explanation_Allergens: str


class ProductNutritionData(BaseModel): 

    Product_Name_Scraped: str
    Serving_Size: str
    
    Servings_Per_Container:str
    Calories: str
    Total_Fat: str
    Saturated_Fat: str
    Trans_Fat: str
    Cholesterol: str
    Sodium: str
    Total_Carbohydrate: str
    Dietary_Fiber: str
    Total_Sugars: str
    Added_Sugars: str
    Protein: str
    
    log: str

class FinalProductNutritionData(ProductNutritionData): 

    Primary_Nutrition_URL: str
    Secondary_Nutrition_URL: List[str]
    Confidence_Score_Nutrition: float
    Confidence_Explanation_Nutrition: str
    Product_Image_Paths_Nutrition: List[str]


class ProductNameValidator(BaseModel):
    is_match: bool
    explanation: str
    product_type_a: str
    product_brand_a: str
    product_flavor_a: str
    product_type_b: str
    product_brand_b: str
    product_flavor_b: str    

class ProductNameData(BaseModel):
    product_name_parsed: str
    explanation: str