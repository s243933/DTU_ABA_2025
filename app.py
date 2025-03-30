import streamlit as st
from PIL import Image

# Set page title and icon
st.set_page_config(page_title="Anti-Food Waste Recommender", page_icon="🥦", layout="centered")

# Load and display a hero image - should I keep it?
hero_image = Image.open("Images/food_waste_hero.jpg") 
st.image(hero_image, use_container_width=True)

# Title and description
st.title("🥕 Anti-Food Waste Recommender")
st.subheader("Turn your leftover ingredients into delicious meals!")

st.markdown(
    """
    🌍 **Did you know?** Over **1.3 billion tons** of food is wasted every year! 
    Instead of throwing away near-expiry ingredients, let’s turn them into amazing recipes. 
    
    👉 **Enter the ingredients manually**, and get an instant recipe recommendation!

    🍽️ The recipes in our database are general, but we also include **some country-specific recipes** to broaden your tastings!
    """,
    unsafe_allow_html=True,
)

# Ingredient Input Section
st.header("🥬 Enter Ingredients")

# Manual ingredient input
ingredients = st.text_area("Or type your ingredients (comma-separated)", placeholder="e.g., tomatoes, onions, garlic")

# Call-to-Action Button
if st.button("Find Recipes 🍽️"):
    if ingredients:
        st.success("🔍 Searching for the best recipes...")  # Placeholder action
    else:
        st.warning("Please upload an image or enter ingredients to continue.")
