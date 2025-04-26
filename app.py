# Imports
import json
import pandas as pd
from PIL import Image
import streamlit as st
# ----------------------------------------------------

# Set page title and icon
st.set_page_config(page_title="Anti-Food Waste Recommender", page_icon="🥦", layout="centered")

# Display a motivational image in the beginning of the page
hero_image = Image.open("Images/food_waste_hero.jpg")
st.image(hero_image, use_container_width=True)

# Title and description
st.title("🥕 Anti-Food Waste Recommender")
st.subheader("Turn your leftover ingredients into delicious meals!")

st.markdown(
    """
    🌍 *Did you know?* Over *2.5 billion tons* of food is wasted every year! ¹ 
    Instead of throwing away near-expiry ingredients, you can easily turn them into amazing recipes. 
    
    👉 *Enter the ingredients manually*, and get an instant recipe recommendation!

    🍽️ Our recipe database covers over EDIT recipes from all over the world, from your *comfort food* to some *country-specific recipes* to broaden your tastings!

    ¹ *Source: [RTS Food Waste in America in 2025](https://www.rts.com/resources/guides/food-waste-america/)*
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

# Function to find recipes that use only heat-processed ingredients matching user input
def find_heat_processed_ingredient(mock_df, ingredient_names, vegan=False, vegetarian=False):
    result = []

    # Loop through each recipe row in the dataframe
    for index, row in mock_df.iterrows():
        # Check dietary restrictions: skip if vegan/vegetarian is required and the recipe doesn't match
        if (vegan and not row['vegan']) or (vegetarian and not row['vegetarian']):
            continue  # Skip this recipe if it doesn't match the restrictions
        try:
            ingredients = json.loads(row['ingredients_processed'])
        except (json.JSONDecodeError, TypeError) as e:
            continue  # Skip this row if parsing fails

        all_ingredients_matched = True # Assume all user ingredients match initially

        # For each ingredient the user entered
        for user_input_ingredient in ingredient_names:
            ingredient_found = False
            # Go through all ingredients listed in the recipe
            for ingredient in ingredients:
                if isinstance(ingredient, dict) and 'name' in ingredient and 'heat_processed' in ingredient:
                    # Match ingredient name and ensure it is heat-processed
                    if match_ingredient(ingredient['name'], user_input_ingredient) and ingredient['heat_processed']:
                        ingredient_found = True
                        break # No need to search further if matched

            # If the current user input ingredient was not found in the recipe, then reject this recipe
            if not ingredient_found:
                all_ingredients_matched = False
                break
        # If all user ingredients are matched in the recipe, add the recipe to the result
        if all_ingredients_matched:
            result.append(row)
    return result

# Ask the user if they have any dietary restrictions
vegan_input = st.radio("Are you vegan?", ('Yes', 'No'), index=None)
vegetarian_input = st.radio("Are you vegetarian?", ('Yes', 'No'), index=None)

# Set vegan and vegetarian flags only if user made a selection
vegan = vegan_input == 'Yes' if vegan_input is not None else None
vegetarian = vegetarian_input == 'Yes' if vegetarian_input is not None else None

# Ingredient input
st.header("🥬 Enter Ingredients")
st.warning("⚠️ Be careful with spelling mistakes!")
ingredients = st.text_area("Enter your ingredients (comma-separated)", placeholder="e.g., tomatoes, onions, garlic")

# Button to trigger recipe search
if st.button("Find Recipes 🍽️"):

    # Check if the user has answered vegan/vegetarian questions
    if vegan is None or vegetarian is None:
        st.warning("Please answer both vegan and vegetarian questions before proceeding.")
    else:
        if ingredients:
            # Normalize and clean up user input ingredients
            ingredient_names = [normalize_ingredient_name(ingredient.strip()) for ingredient in ingredients.split(',')]
            # Load recipe data
            mock_df = pd.read_csv('receipts_table.csv')
            mock_df = mock_df[mock_df["heat_processed"] == True] # Filter only heat-processed recipes
            
            # Find matching recipes based on ingredients and dietary restrictions
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

                # Show detailed info for each recipe
                for i, selected_recipe in enumerate(matching_recipes, 1):
                    st.write(f"## **Recipe {i}: {selected_recipe['title']}**")
                    
                    # Display the ingredients for the corresponding recipe
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
                    
                    # Display instructions for the recipe
                    st.write(f"**Instructions**:")
                    st.write(selected_recipe['instructions'])

                    # Add a separating line after each recipe
                    st.markdown("<hr>", unsafe_allow_html=True)
            else:
                # No recipes found
                st.warning("No matching recipes found.")
        else:
            # User didn't enter any ingredients
            st.warning("Please enter ingredients to search for recipes.")
