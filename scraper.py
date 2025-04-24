# Load imports
from recipe_scrapers import scrape_me, scrape_html
import requests

from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

import pandas as pd
import regex as re
import time
from tqdm import tqdm



# Read a single recipe from the recipe URL
def read_recipe(page_url, a):
    """
    Read a single recipe from the recipe URL.
    Args:
        page_url (str): The URL of the page containing the recipe.
        a (BeautifulSoup object): The anchor tag containing the recipe link.
    Returns:
        dict: A dictionary containing the recipe title, ingredients, and instructions if any, else None.
    """
    try:
        href = a['href']
        recipe_url = urljoin(page_url, href)

        # Scrape the actual recipe
        scraped = scrape_me(recipe_url)

        # If there is no title, return None
        if scraped.title() != None and scraped.title() != 'None' and scraped.title() != '':    

            try:
                recipe = {'Title': scraped.title(), 'Ingredients': scraped.ingredients(), 'Instructions': scraped.instructions(), 'URL': recipe_url}
                return recipe
            
            except Exception as e:
                print(f"Error scraping recipe {recipe_url}: {e}")
                return None
            
        else:
            return None
        
    except Exception as e:
        print(f"Error scraping recipe {recipe_url}: {e}")
        return None


# Check if there are any recipes on the page URL
def check_if_recipes_on_page(page_url, page_soup):
    """
    Check if there are any recipes on the page URL by either
    1. Looking for the class 'recipe-title' in the anchor tags, or,
    2. Looking for the class 'page' in the anchor tags, or,
    3. Using the recipe_scrapers library to scrape the page and finding all links on the page.
    Args:
        page_url (str): The URL of the page to check.
        page_soup (BeautifulSoup object): The BeautifulSoup object of the page.
    Returns:
        list: A list of anchor tags containing the recipes on the page or all links on the page if any, else None.
    """
    try:
        recipes_on_page = page_soup.findAll('a', {'class': lambda x: x and 'recipe-title' in x.split()})

        if len(recipes_on_page) == 0:
            recipes_on_page = page_soup.findAll('a', {'class': lambda x: x and 'page' in x.split()})

            if len(recipes_on_page) == 0:
                recipes_on_page = scrape_me(page_url).links()

        return recipes_on_page
    
    except Exception as e:
        print(f"Error checking recipes on page: {e}")
        return None


# Read all the recipes on the paritcular page URL
def read_recipes_on_page(page_url):
    """
    Read all the recipes on the page URL.
    Args:
        page_url (str): The URL of the page to read recipes from.
    Returns:
        list: A list of dictionaries containing the recipes on the page if any, else None.
    """
    try:
        page_response = requests.get(page_url)
        page_soup = BeautifulSoup(page_response.text, "html.parser")

        recipes = []
        
        if page_soup:
        
            recipes_on_page = check_if_recipes_on_page(page_url, page_soup)
            
            for a in tqdm(recipes_on_page):
                recipe = read_recipe(page_url, a)

                if recipe != None:
                    recipes.append(recipe)

                    # To avoid server timeouts
                    time.sleep(1)
                else:
                    continue
            
            return recipes
        
        else:
            return None
    
    except Exception as e:
        print(f"Error reading recipes on page: {e}")
        return None


# Finding the next page in a website
def find_next_page(page_refs, next_page, recipes_url):
    """
    Find the next page in a website.
    Args:
        page_refs (list): A list of anchor tags containing the next page links.
        next_page (int): The next page number to find.
        recipes_url (str): The base URL of the recipes website.
    Returns:
        str: The URL of the next page if found, otherwise None.
    """
    if len(page_refs) > 0:

        for i, page_ref in enumerate(page_refs):

            # Check whether the string contain a 'href' tag
            href = re.search(r'(href="[^"]*")', page_ref)
            # Extract only the href tag from the string
            clean_href = href.group(0).replace('href="', '').replace('"', '')

            if re.search(r'(\d+)', clean_href).group(0) == str(next_page):
                page_url = urljoin(recipes_url, clean_href.split('/recipes/')[-1])
                
                return page_url
    
    else:
        return None


# Going to the next page in a website
def go_to_next_page(recipes_url, next_page):
    """
    Go to the next page in a website.
    Args:
        recipes_url (str): The base URL of the recipes website.
        next_page (int): The next page number to find.
    Returns:
        str: The URL of the next page if found, otherwise None.
    """
    recipe_page_response = requests.get(recipes_url)
    recipe_page_soup = BeautifulSoup(recipe_page_response.text, "html.parser")
    page_html = str(recipe_page_soup.prettify()).split('<')

    # Check if any of the references contain the string 'page' or 'next'
    page_refs = [val for val in page_html if re.search(r"(([Pp][Aa][Gg][Ee]).?\d+)", val)]

    if len(page_refs) == 0:
        page_refs = [val for val in page_html if re.search(r"(([Nn][Ee][Xx][Tt]).?\d+)", val)]
    
    next_page_url = find_next_page(page_refs, next_page, recipes_url)

    if next_page_url:
        return next_page_url
    else:
        return None

# Read all the recipes from the website
def read_all_recipes_on_url(recipes_url):
    """
    Read all the recipes from the website.
    Args:
        recipes_url (str): The base URL of the recipes website.
    Returns:
        list: A list of dictionaries containing all the recipes on the website.
    """
    curr_page = 1   # Set current page and increment it by 1 for each page
    last_page = False

    all_recipes = []

    # While there are still pages to read
    while not last_page:

        try:
            # If the current page is 1, use the base URL, otherwise go to the next page
            if curr_page == 1:
                page_url = recipes_url
            else:
                page_url = go_to_next_page(page_url, curr_page)
            
            print(f'Page {curr_page}: {page_url}')
            recipes = read_recipes_on_page(page_url)

            # If there there are recipes on the page, increment the page number, else break the loop
            if recipes:
                all_recipes.extend(recipes)
                curr_page += 1
            else:
                last_page = True
            
        except Exception as e:
            print(f"Error reading recipes on page {curr_page}: {e}")
            last_page = True

        # IMPORTANT: Set a maximum page limit to avoid infinite loops!!!!
        if curr_page == 100:
            print("Reached maximum page limit.")
            last_page = True
            
    return all_recipes


# Get all website URLs from scraper pypi source documentation
def get_all_website_urls():
    """
    Get all website URLs from the scraper pypi source documentation at "https://pypi.org/project/recipe-scrapers-ap-fork/".
    Returns:
        list: A list of website URLs.
    """
    page_response = requests.get("https://pypi.org/project/recipe-scrapers-ap-fork/")
    page_soup = BeautifulSoup(page_response.text, "html.parser")
    page_html = str(page_soup.prettify()).split('<')

    websites = []

    for item in page_html:

        # Checks to make sure we only extract cooking websites
        if 'rel="nofollow"' in item and 'https' in item and not any(val in item for val in ['pypi', 'github', 'pepy', 'python', 'project']):
            href = re.search(r'(href="[^"]*")', item)
            clean_href = href.group(0).replace('href="', '').replace('"', '')
            websites.append(clean_href)
    
    return websites


# Define main function to run the scraper
def main():
    
    # Get all website URLs
    websites = get_all_website_urls()

    # Store all recipes
    all_recipes = []

    # Make sure there are websites to scrape
    if websites:

        # Loop through each website and scrape the recipes
        for website in websites:

            print(f"Scraping recipes from {website}...")
            recipes = read_all_recipes_on_url(website)

            if recipes:
                all_recipes.extend(recipes)
                print(f"Scraped {len(recipes)} recipes from {website}.")
            else:
                print(f"No recipes found on {website}.")
    
    # Make a dataframe from the recipes
    df = pd.DataFrame.from_records(all_recipes)
    # Drop duplicate recipes based on the title
    df_sub = df.drop_duplicates(subset=['Title'], keep='first')
    # Make sure all columns are populated for a recipe
    df_clean = df_sub[(df_sub['Title']!='None')&(len(df_sub['Ingredients'])!=0)&(df_sub['Instructions']!='')].reset_index(drop=True)

    # Convert df to csv file
    if not os.path.exists('recipes'):
        os.makedirs('recipes')
    df_clean.to_csv('recipes/recipes.csv', index=False)

    return df_clean


if __name__ == "__main__":
    main()
