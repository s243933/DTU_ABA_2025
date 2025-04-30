# interactive hpc commands to run first
# module load python3/3.11.9
# module load cuda/12.8.0
# pip3 install --user pandas transformers torch torchvision torchaudio accelerate bitsandbytes
# python3 process_batch.py recipes_batch_0001.csv LLM/testing_batch_results/recipes_batch_0001.csv


# Import necessary libraries
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import pandas as pd
import sys
import json

# --- Configuration ---
# Model used
MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

# BitsAndBytesConfig to decrease memory usage
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)

# --- Prompt Definition ---
PROMPT_TEMPLATE = """
<instruction>
Analyze the recipe for:
1. Heat processing of ingredients based on cooking instructions.
   Heat processing refers to any ingredient that is exposed to heat during preparation,
   including frying, boiling, sautéing, baking, or any cooking method that raises
   the temperature of the ingredient. Ingredients that are only mixed, soaked in room
   temperature water, or added after cooking are NOT heat processed.
   Provide the output as a JSON array of objects with "ingredient" and "heat_processed" keys.
2. Identify 3 cuisine types that best match this recipe.
   Examples of cuisines include:
   - Regional cuisines: Italian, Mexican, Chinese, Japanese, Korean, Thai
   - Indigenous cuisines: Inuit, Maori, Native American, Aboriginal Australian
   - Fusion cuisines: Tex-Mex, Peranakan, Chifa, Nikkei
   - Island cuisines: Faroese, Canarian, Hawaiian, Okinawan
   Provide the output as a JSON array of strings.
</instruction>

<input>
Ingredients:
{ingredients}

Instructions:
{instructions}
</input>

<output_format>
{{
  "heat_processing": [{{"ingredient": "name", "heat_processed": true/false}}],
  "cuisine_types": ["cuisine1", "cuisine2", "cuisine3"]
}}
</output_format>

<output>
""" 

# --- Command-Line Argument Handling ---
# Check if the correct number of command-line arguments are provided
if len(sys.argv) != 3:
    print("Usage: python process_batch.py <input_csv_path> <output_csv_path>")
    sys.exit(1)

# Get input and output file paths from command-line arguments
input_csv_path = sys.argv[1]
output_csv_path = sys.argv[2]

print(f"Input batch file: {input_csv_path}")
print(f"Output results file: {output_csv_path}")

# --- Load the Batch Data ---
try:
    # Read the input CSV file into a pandas DataFrame
    df = pd.read_csv(input_csv_path)
    print(f"Successfully loaded {len(df)} recipes from {input_csv_path}")

    # Check if the DataFrame is empty
    if df.empty:
        print("Warning: Input CSV is empty. Nothing to process.")
        sys.exit(0)

    # Ensure necessary columns exist
    required_cols = ['ingredients_raw', 'instructions']
    if not all(col in df.columns for col in required_cols):
        print(f"Error: Input CSV must contain columns: {required_cols}")
        sys.exit(1)

    # Add/ensure output columns exist
    if 'ingredients_processed' not in df.columns:
        df['ingredients_processed'] = None
    if 'cuisine_tags' not in df.columns:
        df['cuisine_tags'] = None
    # Column to flag processing errors for a recipe
    if 'processing_error' not in df.columns:
         df['processing_error'] = None


except FileNotFoundError:
    print(f"Error: Input file not found at {input_csv_path}")
    sys.exit(1)
except Exception as e:
    print(f"Error loading input CSV {input_csv_path}: {e}")
    sys.exit(1)


# --- Load Model and Tokenizer ---
print(f"\nAttempting to load model from Hugging Face Hub: {MODEL_NAME}")

try:
    # Load the tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    print("Tokenizer loaded.")

    # Load the model with quantization
    print(f"Loading model {MODEL_NAME}...")
    # Determine the device to use (GPU if available, otherwise CPU)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        low_cpu_mem_usage=True if device == "cpu" else False,
        torch_dtype=torch.bfloat16 if device == "cuda" and torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8 else torch.float32 # Use bfloat16 on newer GPUs
    )
    print("Model loaded.")

    # Move the model to the selected device
    model.to(device)
    print("Model moved to device.")

    # Set the model to evaluation mode
    model.eval()

except Exception as e:
    print(f"\n--- Model Loading Error ---")
    print(f"An error occurred during model loading: {e}")
    print("Please ensure:")
    print(f"1. The necessary Python libraries (transformers, torch, pandas, sys, json) are installed.")
    print(f"2. The HPC node has network access to download model weights from Hugging Face Hub (or they are cached).")
    print(f"3. The requested memory and CPU/GPU resources are sufficient for the model.")
    # Exit with a non-zero status to indicate failure
    sys.exit(1)


# --- Processing Loop (Iterate through each recipe in the batch) ---
print("\n--- Starting Batch Processing ---")

# Iterate over rows of the DataFrame
for index, row in df.iterrows():
    try:
        # Get ingredients and instructions for the current recipe
        ingredients = row['ingredients_raw']
        instructions = row['instructions']

        # Construct the full prompt for the current recipe
        current_prompt = PROMPT_TEMPLATE.format(
            ingredients=ingredients,
            instructions=instructions
        )

        # Prepare the input for the model
        if tokenizer.chat_template:
             messages = [
                {"role": "system", "content": "You are a precise recipe analyzer. Focus on determining ingredient heat processing and identifying cuisine types. Provide output strictly in the specified JSON format, do NOT include the quantity of the ingredient."},
                {"role": "user", "content": current_prompt}
            ]
             # Apply the chat template to format the messages into a single string
             input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        else:
             # Fallback to a simple prompt format if no chat template is defined
             input_text = f"Instruct: {current_prompt}\nOutput:"

        # Tokenize the input and move to the correct device
        input_ids = tokenizer(input_text, return_tensors="pt").to(device)

        # Generate a response from the model
        with torch.no_grad():
            output_ids = model.generate(
                input_ids.input_ids,
                max_new_tokens=2000, # the output length
                pad_token_id=tokenizer.eos_token_id,
            )

        # Decode the generated response
        model_response_content = tokenizer.decode(output_ids[0][input_ids.input_ids.shape[1]:], skip_special_tokens=True)

        # --- Parse the Model's JSON Output ---
        json_start = model_response_content.find('{')
        json_end = model_response_content.rfind('}')

        parsed_heat_processing = None
        parsed_cuisine_tags = None
        processing_error = None

        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_string = model_response_content[json_start : json_end + 1]
            try:
                # Attempt to parse the extracted JSON string
                parsed_output = json.loads(json_string)

                # Extract heat processing data
                if 'heat_processing' in parsed_output and isinstance(parsed_output['heat_processing'], list):
                    parsed_heat_processing = json.dumps(parsed_output['heat_processing'])

                # Extract cuisine tags
                if 'cuisine_types' in parsed_output and isinstance(parsed_output['cuisine_types'], list):
                    parsed_cuisine_tags = json.dumps(parsed_output['cuisine_types'])
                else:
                    processing_error = "Cuisine types not found or not list in JSON"

            except json.JSONDecodeError as e:
                processing_error = f"JSON parsing failed: {e}"
                print(f"JSON parsing failed for recipe at index {index}: {e}")
                print(f"Raw model response snippet: {model_response_content[:500]}...")
            except Exception as e:
                processing_error = f"Error processing parsed JSON: {e}"
                print(f"Error processing parsed JSON for recipe at index {index}: {e}")

        else:
            processing_error = "JSON structure not found in model response"
            print(f"JSON structure not found in model response for recipe at index {index}.")
            print(f"Raw model response snippet: {model_response_content[:500]}...") 

        # --- Update DataFrame with Results ---
        # .loc to update the specific row by index
        df.loc[index, 'ingredients_processed'] = parsed_heat_processing
        df.loc[index, 'cuisine_tags'] = parsed_cuisine_tags
        df.loc[index, 'processing_error'] = processing_error

        # Progress every 10 recipes
        if (index + 1) % 10 == 0:
            print(f"Processed {index + 1}/{len(df)} recipes in this batch.")

    except Exception as e:
        # Catch any unexpected errors during processing of a single recipe
        print(f"An unexpected error occurred processing recipe at index {index}: {e}")
        df.loc[index, 'processing_error'] = f"Unexpected error: {e}"

print("Batch processing complete.")


# --- Save the Processed Data ---
print(f"\n--- Saving Results to {output_csv_path} ---")
try:
    # Save the entire DataFrame with the new columns
    df.to_csv(output_csv_path, index=False)
    print("Results saved successfully.")
except Exception as e:
    print(f"Error saving results to {output_csv_path}: {e}")
    sys.exit(1)

# --- Script Finished ---
print("Script finished successfully.")
sys.exit(0)
