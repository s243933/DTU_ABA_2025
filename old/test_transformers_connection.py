# Import necessary libraries
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# --- Configuration ---
# Model used
MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

# BitsAndBytesVonfig to decrease memory usage
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)

# --- Prompt ---
TEST_PROMPT = """
<instruction>
Analyze the recipe for:
1. Heat processing of ingredients based on cooking instructions.
   Heat processing refers to any ingredient that is exposed to heat during preparation,
   including frying, boiling, sautéing, baking, or any cooking method that raises
   the temperature of the ingredient. Ingredients that are only mixed, soaked in room 
   temperature water, or added after cooking are NOT heat processed.
2. Identify 3 cuisine types that best match this recipe.
   Examples of cuisines include:
   - Regional cuisines: Italian, Mexican, Chinese, Japanese, Korean, Thai
   - Indigenous cuisines: Inuit, Maori, Native American, Aboriginal Australian
   - Fusion cuisines: Tex-Mex, Peranakan, Chifa, Nikkei
   - Island cuisines: Faroese, Canarian, Hawaiian, Okinawan
   - Diaspora cuisines: Chinese-American, Korean-Japanese, Indian-British
</instruction>

<input>
Ingredients:
8 oz rice noodles
3 tbsp vegetable oil
2 eggs, lightly beaten
2 cloves garlic, minced
1 carrot, julienned
1 red bell pepper, thinly sliced
100g bean sprouts
3 tbsp soy sauce
2 tbsp brown sugar
2 tbsp lime juice
1 tbsp sriracha
1/4 cup chopped peanuts
3 green onions, sliced
1/4 cup cilantro leaves

Instructions:
Soak rice noodles in hot water for 10 minutes until softened, then drain. Heat 1 tbsp oil in a wok over high heat. Add eggs and scramble until set, then transfer to a plate. Add remaining oil to wok. Stir-fry garlic for 30 seconds, then add carrot and bell pepper for 2 minutes. Add noodles, soy sauce, sugar, lime juice, and sriracha; stir-fry for 3 minutes. Mix in eggs and bean sprouts. Top with peanuts, green onions, and cilantro before serving.
</input>

<output_format>
{
  "heat_processing": [{"ingredient": "name", "heat_processed": true/false}],
  "cuisine_types": ["cuisine1", "cuisine2", "cuisine3"]
}
</output_format>

<output>
"""

# --- Run the Test ---
if __name__ == "__main__":
    print(f"Attempting to load model from Hugging Face Hub: {MODEL_NAME}")

    try:
        # Load the tokenizer
        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        print("Tokenizer loaded.")

        # Load the model with quantization
        print(f"Loading model {MODEL_NAME} with 4-bit quantization...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")

        # to lower memory on CPU
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            low_cpu_mem_usage=True, 
        )
        print("Model loaded.")

        model.to(device)
        print("Model moved to device.")


        # Input for the model
        if tokenizer.chat_template:
             messages = [
                {"role": "system", "content": "You are a precise recipe analyzer. Focus on determining ingredient heat processing and identifying cuisine types."},
                {"role": "user", "content": TEST_PROMPT}
            ]

             input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        else:
             # Fallback to a simple prompt format
             input_text = f"Instruct: {TEST_PROMPT}\nOutput:"


        print(f"Sending test prompt: '{input_text}'")

        # Tokenize the input
        input_ids = tokenizer(input_text, return_tensors="pt").to(device)

        # Generate a response
        print("Generating response...")
        output_ids = model.generate(input_ids.input_ids, max_new_tokens=2000)

        # Decode the response
        model_response_content = tokenizer.decode(output_ids[0], skip_special_tokens=True)

        print("\n--- Model Response ---")
        print(model_response_content)
        print("\n--- Test Complete ---")

    except Exception as e:
        print(f"\n--- Error ---")
        print(f"An error occurred: {e}")
        print("Please ensure:")
        print(f"1. The necessary Python libraries (transformers, torch, accelerate) are installed.")
        print(f"2. The HPC node has network access to download model weights from Hugging Face Hub.")
        print(f"3. The requested memory and CPU resources are sufficient for the model.")
        # Exit with a non-zero status to indicate failure
        exit(1)

