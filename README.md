![Alt text](app/food_waste_hero.jpg?raw=true "Title")

# Anti-Food Waste Recommendation System

## Project Overview

Food waste is a serious global issue, with huge amount of edible food thrown away every year. Our project aims to help individuals, food sharing platforms, and supermarkets reduce waste by suggesting recipes using ingredients near their expiration date. For raw ingredients like vegetables or fruits, a user would ideally not want to consume a not-so-fresh version of them in their raw form. For example, if a user wants to use a not-so-fresh tomato, they would not want to see recipes of salads which is what they might see if they were to use a generic recipe recommeder. This is because they do not take into account the freshness of an ingredient. Our sustainable alternative takes the freshness of an ingredient into account and provides a reasonable recipe output!

## Accessing the App
In order to access our recipe recommendation system, clone the repository, and run the following command within the main repository folder: `streamlit run app/app.py`. Click the localhost link that is outputted, input your preferences, and get the recipes that you are looking for. You are now one step closer to creating a more sustainable world!!


## Project Structure

### Folders

- **`LLM/`**: contains items related to the LLM usage within the project.
  - **`batched_recipes/`**: all of the batched pieces of all recipes. There have 200 recipes in each `csv` file within the folder, hence, there are 18 `csv` files.
    - `recipes_batch_00xx.csv`: contains 200 recipes extracted from the scraping.
  - **`batched_recipes_results/`**: output files after LLM analysis. It consists of 12 `csv` files.
    - `recipes_batch_00xx.csv`: contains the recipes' data *after* LLM analysis.
  - **`tesing/`**: files used to check if the HPC works as intended.
    - `recipes_batch_0001.csv`: ?? (one of the batched recipe files used for testing.)
    - `results_test_batch_0001.csv`: ?? (the result of the testing HPC.)
    - `run_test_batch.lsf`: ?? (the instructions for the HPC to run the batch through the LLM and put it into a queue.)
  - **`testing_batch/`**:  two batches retrieved from initial table for testing purposes.
    - `test_batch_0001.csv`: ??
    - `test_batch_0002.csv`: ??
  - `merged_final_results.csv`: resulting table after merging together all of the files from the LLM analysis in **`batched_recipes_results/`**.
  - `process_batch.py`: the main part of the LLM where the model is run.
  - `recipes_table_prep.ipynb`: where the prep before LLM was done and also merging together the `csv` files after running the LLM.
  - `run_batch_array.sh`: the instructions for the HPC to run all of the batches through the LLM and putting them into queues.
  
- **`app/`**: the files related to our front-end interface.
  - `app.py`: the implementation of the front-end streamlit interface that users can interact with and get recipe recommendations.
  - `food_waste_hero.jpg`: the banner for our project and the front-end.
  
- **`recipes/`**: the outputs from scraping recipes.
    - `english_recipes.csv`: a subset of only english recipes from the overall scraped recipes.
    - `recipes.csv`: the initial output from scraping recipes which is a result of executing `scraping/scraper.py`.

- **`scraping/`**: the files related to scraping recipes online.
  - `get_more_recipes.ipynb`: the scraping notebook where all functions are documented with descriptions for each function for the scraping functionality. The outputted recipes are also subsetted to get only the recipes that are in English.
  - `scraper.py`: the python script that is used within the job file for the HPC.
  - `scraper_job.bsub`: the file used to queue a job to the HPC.
  - `scraper_requirements.txt`: the libraries used for scraping only.

### Files
- `one_pager_group4.pdf`: a short abstract explaining our *initial* objective, scope, datasets, and course-related topics to be used within the project.
- `report_group4.ipynb`: the technical report with descriptions of how the project was executed.
- `executive_summary_group4.pdf`: a one page file aimed at communicating our project to a non-technical business audience.
- `individual_contributions.pdf`: a file containing contributions of members to the different areas within the project.
