# To be able to run this script and see our app implemented, please run the following in a terminal:
#   > streamlit run app/app.py

# Imports
import ast
import json
import pandas as pd
from PIL import Image
import streamlit as st
# ----------------------------------------------------

# Set page title and icon
st.set_page_config(page_title="Anti-Food Waste Recommender", page_icon="🥦", layout="centered")

# Display a motivational image in the beginning of the page
hero_image = Image.open("app/food_waste_hero.jpg")
st.image(hero_image, use_container_width=True)

# Title and description
st.title("🥕 Anti-Food Waste Recommender")
st.subheader("Turn your leftover ingredients into delicious meals!")

st.markdown(
    """
    🌍 *Did you know?* Over *2.5 billion tons* of food is wasted every year! ¹ 
    Instead of throwing away near-expiry ingredients, you can easily turn them into amazing recipes. 
    
    👉 *Enter the ingredients manually*, and get an instant recipe recommendation!

    🍽️ Our recipe database covers over 2,300 recipes from all over the world, from your *comfort food* to some *country-specific recipes* to broaden your tastings!

    ¹ *Source: [RTS Food Waste in America in 2025](https://www.rts.com/resources/guides/food-waste-america/)*
    """,
    unsafe_allow_html=True,
)

# Function to normalize ingredient names
def normalize_ingredient_name(name):
    name = name.lower().strip()
    if name.endswith('s') and not name.endswith('ss'):
        name = name[:-1]  # Remove plural s
    return name

# Function to match ingredients in the recipe
def match_ingredient(ingredient_name, user_input_ingredient):
    ing = normalize_ingredient_name(ingredient_name)
    user_ing = normalize_ingredient_name(user_input_ingredient)

    if len(user_ing.split()) == 1:
        return user_ing in ing  # single word: partial match allowed
    else:
        return ing == user_ing  # multi-word: exact match only

# Ask the user if they have any dietary restrictions
vegan_input = st.radio("Are you vegan? *", ('Yes', 'No'), index=None)
vegetarian_input = st.radio("Are you vegetarian?*", ('Yes', 'No'), index=None)

# Set vegan and vegetarian flags only if user made a selection
vegan = vegan_input == 'Yes' if vegan_input is not None else None
vegetarian = vegetarian_input == 'Yes' if vegetarian_input is not None else None

# Define valid cuisine whitelist
CUISINE_WHITELIST = {
    'American', 'Argentinian', 'Asian', 'Asian Fusion', 'Australian', 'Brazilian', 'British',
    'Cajun', 'Canadian', 'Caribbean', 'Chinese', 'Contemporary', 'Contemporary American', 'Contemporary European', 'Contemporary French', 'Contemporary Italian', 'Continental', 'Creole', 'Cuban',
    'Dutch', 'English', 'European', 'Far Eastern', 'Faroe Islands', 'Finnish', 'French', 'German', 'French', 'French Polynesia', 'French-inspired', 'Global',
    'Goan', 'Greek', 'Gujarati', 'Hawaiian', 'Hyderabadi', 'Indian', 'Indian-American', 'Indian-Caribbean', 'Indigenous', 'Indigenous cuisines',
    'Indo-Caribbean', 'Indonesian', 'Iranian', 'Irish', 'Israeli', 'Italian', 'Jamaican', 'Indo-Anglo', 'Indo-British', 'Indo-Caribbean', 'Indo-Chinese', 'Indo-French', 'Indo-Pakistani', 'Indo-Spanish',
    'Japanese', 'Kashmiri', 'Korean', 'Latin American', 'Lebanese', 'Malaysian', 'International', 'Island cuisines', 'Regional cuisines', 'United Kingdom', 'Western (Paleo)',
    'Mangalorean', 'Mediterranean', 'Mexican', 'Middle Eastern', 'Moroccan', 'Neapolitan',
    'North African', 'North American', 'Pakistani', 'Peranakan', 'Persian', 'Peruvian',
    'Polish', 'Provence', 'Scandinavian', 'Scottish', 'Singaporean', 'Slavic',
    'South American', 'South Asian', 'South Indian', 'Southeast Asian', 'Southern',
    'Southwestern', 'Spanish', 'Tex-Mex', 'Thai', 'Vietnamese', 'West African', 'Western'
}

# Load once for tag extraction
df_preview = pd.read_csv('LLM/merged_final_results.csv')

# Extract cuisines and other tags
cuisine_set = set()
other_tag_set = set()

for val in df_preview['cuisine_tags'].dropna():
    try:
        tags = json.loads(val) if isinstance(val, str) else val
        if isinstance(tags, list):
            for tag in tags:
                tag_clean = tag.strip()
                if tag_clean in CUISINE_WHITELIST:
                    cuisine_set.add(tag_clean)
                elif tag_clean not in {"Vegan", "Vegetarian"}:
                    other_tag_set.add(tag_clean)
    except Exception:
        continue

# UI: user selects cuisine types and other tags
selected_cuisines = st.multiselect("🌍 Filter by Cuisine Type (you can select multiple options)", sorted(cuisine_set))
selected_other_tags = st.multiselect("🏷️ Filter by Other Tags (you can select multiple options)", sorted(other_tag_set))

# Function to find recipes that use only heat-processed ingredients matching user input
def find_heat_processed_ingredient(df, ingredient_names, vegan=False, vegetarian=False):
    result = []

    # Loop through each recipe row in the dataframe
    for index, row in df.iterrows():
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
                if isinstance(ingredient, dict) and 'ingredient' in ingredient and 'heat_processed' in ingredient:
                    # Match ingredient name and ensure it is heat-processed
                    if match_ingredient(ingredient['ingredient'], user_input_ingredient) and ingredient['heat_processed']:
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
            df = pd.read_csv('LLM/merged_final_results.csv')

            # Filter recipes by cuisine or tag selections
            def recipe_matches_filters(row):
                try:
                    tags = json.loads(row['cuisine_tags']) if isinstance(row['cuisine_tags'], str) else row['cuisine_tags']
                    tags_set = set(tags)
                    cuisine_ok = not selected_cuisines or any(tag in tags_set for tag in selected_cuisines)
                    other_ok = not selected_other_tags or any(tag in tags_set for tag in selected_other_tags)

                    return cuisine_ok and other_ok
                except Exception:
                    return False

            df = df[df.apply(recipe_matches_filters, axis=1)]

            # Convert string "TRUE"/"FALSE" to boolean True/False
            df['vegan'] = df['vegan'].astype(str).str.lower().map({'true': True, 'false': False})
            df['vegetarian'] = df['vegetarian'].astype(str).str.lower().map({'true': True, 'false': False})

            # Fix wrongly labeled recipes that mention steak
            df.loc[
                df['ingredients_raw'].str.contains('steak', case=False, na=False),
                ['vegan', 'vegetarian']
            ] = False
            
            # Find matching recipes based on ingredients and dietary restrictions
            matching_recipes = find_heat_processed_ingredient(df, ingredient_names, vegan, vegetarian)
            
            if matching_recipes:
                # Create a list of recipe titles
                recipe_titles = [recipe['title'] for recipe in matching_recipes]

                # Display the bullet list of all matching recipes
                st.markdown("Here are the recipes that match your criteria:")
                for i, recipe_title in enumerate(recipe_titles, 1):
                    anchor_id = f"recipe-{i}"
                    st.markdown(
                        f'<a href="#{anchor_id}" style="color: white">{i}. <strong>{recipe_title}</strong></a>',
                        unsafe_allow_html=True)

                st.markdown("<hr>", unsafe_allow_html=True)
                st.write("Below you can find the corresponding details:")

                # Show detailed info for each recipe
                for i, selected_recipe in enumerate(matching_recipes, 1):
                    st.markdown(f'<a name="recipe-{i}"></a>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <a name="recipe-{i}"></a>
                    ## **Recipe {i}: {selected_recipe['title']}**
                    <a href="#f3fe72f5" style="color: white; font-size: 16px;">🔝 Back to top</a>
                    """, unsafe_allow_html=True)
                    
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
            elif len(ingredient_names) == 1 and len(ingredient_names[0].split()) > 1:
                st.warning("No matching recipes found. Try shortening your ingredient(s) name to a more general term.")
            else:
                st.warning("No matching recipes found.")

        else:
            # User didn't enter any ingredients
            st.warning("Please enter ingredients to search for recipes.")