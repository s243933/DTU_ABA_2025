import streamlit as st
import json
import pandas as pd
from PIL import Image

# Set page title and icon
st.set_page_config(page_title="Anti-Food Waste Recommender", page_icon="🥦", layout="centered")

# Load and display a hero image
hero_image = Image.open("Images/food_waste_hero.jpg")
st.image(hero_image, use_container_width=True)

# Title and description
st.title("🥕 Anti-Food Waste Recommender")
st.subheader("Turn your leftover ingredients into delicious meals!")

st.markdown(
    """
    🌍 *Did you know?* Over *1.3 billion tons* of food is wasted every year! 
    Instead of throwing away near-expiry ingredients, let’s turn them into amazing recipes. 
    
    👉 *Enter the ingredients manually*, and get an instant recipe recommendation!

    🍽️ The recipes in our database are general, but we also include *some country-specific recipes* to broaden your tastings!
    """,
    unsafe_allow_html=True,
)

# Function to normalize ingredient names
def normalize_ingredient_name(ingredient_name):
    if ingredient_name.endswith('s'):
        ingredient_name = ingredient_name[:-1]
    return ingredient_name.lower()

# Function to match ingredients in the recipe
def match_ingredient(ingredient_name, user_input_ingredient):
    normalized_ingredient = normalize_ingredient_name(ingredient_name)
    normalized_user_input = normalize_ingredient_name(user_input_ingredient)
    ingredient_words = set(normalized_ingredient.split())  # Split the ingredient into words
    user_input_words = set(normalized_user_input.split())  # Split the user input into words
    return bool(ingredient_words & user_input_words)

# Function to find heat processed ingredients
def find_heat_processed_ingredient(mock_df, ingredient_names, vegan=False, vegetarian=False):
    result = []
    for index, row in mock_df.iterrows():
        if (vegan and not row['vegan']) or (vegetarian and not row['vegetarian']):
            continue  # Skip this recipe if it doesn't match the restrictions
        try:
            ingredients = json.loads(row['ingredients_processed'])
        except (json.JSONDecodeError, TypeError) as e:
            continue  # Skip this row if parsing fails
        all_ingredients_matched = True
        for user_input_ingredient in ingredient_names:
            ingredient_found = False
            for ingredient in ingredients:
                if isinstance(ingredient, dict) and 'name' in ingredient and 'heat_processed' in ingredient:
                    if match_ingredient(ingredient['name'], user_input_ingredient) and ingredient['heat_processed']:
                        ingredient_found = True
                        break
            if not ingredient_found:
                all_ingredients_matched = False
                break
        if all_ingredients_matched:
            result.append(row)
    return result

# Ask the user if they have any dietary restrictions
vegan_input = st.radio("Are you vegan?", ('Yes', 'No'))
vegetarian_input = st.radio("Are you vegetarian?", ('Yes', 'No'))

vegan = vegan_input == 'Yes'
vegetarian = vegetarian_input == 'Yes'

# Ingredient input
st.header("🥬 Enter Ingredients")
st.warning("⚠️ Be careful with spelling mistakes!")
ingredients = st.text_area("Enter your ingredients (comma-separated)", placeholder="e.g., tomatoes, onions, garlic")

if st.button("Find Recipes 🍽️"):
    if ingredients:
        ingredient_names = [normalize_ingredient_name(ingredient.strip()) for ingredient in ingredients.split(',')]
        
        mock_df = pd.read_csv('receipts_table.csv')
        mock_df = mock_df[mock_df["heat_processed"] == True]
        
        matching_recipes = find_heat_processed_ingredient(mock_df, ingredient_names, vegan, vegetarian)
        
        if matching_recipes:
            # Create a list of recipe titles
            recipe_titles = [recipe['title'] for recipe in matching_recipes]

            # Display the bullet list of all matching recipes
            st.markdown("Here are the recipes that match your criteria:")
            for i, recipe_title in enumerate(recipe_titles, 1):
                st.markdown(f"- {i}. **{recipe_title}**")

            st.markdown("<hr>", unsafe_allow_html=True)
            st.write("Below you can find the corresponding details:")

            # Show detailed information for each recipe
            for i, selected_recipe in enumerate(matching_recipes, 1):
                st.write(f"## **Recipe {i}: {selected_recipe['title']}**")
                
                # Display the ingredients for the recipe
                st.write(f"**Ingredients**:")
                ingredients_raw_str = selected_recipe.get('ingredients_raw', '')
                
                if isinstance(ingredients_raw_str, str) and ingredients_raw_str.startswith('[') and ingredients_raw_str.endswith(']'):
                    try:
                        ingredients_raw_list = eval(ingredients_raw_str)  # Using eval to convert the string to a list
                        for ingredient in ingredients_raw_list:
                            st.write(f"- {ingredient}")
                    except Exception as e:
                        st.warning(f"Error processing raw ingredients: {e}")
                elif isinstance(ingredients_raw_str, list):
                    for ingredient in ingredients_raw_str:
                        st.write(f"- {ingredient}")
                else:
                    st.warning("Ingredients data is in an unexpected format.")
                
                # Display the instructions for the recipe
                st.write(f"**Instructions**:")
                st.write(selected_recipe['instructions'])

                # Add a separating line after each recipe
                st.markdown("<hr>", unsafe_allow_html=True)
        else:
            st.warning("No matching recipes found.")
    else:
        st.warning("Please enter ingredients to search for recipes.")
