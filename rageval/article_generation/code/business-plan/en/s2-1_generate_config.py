import sys
import os
import json
from openai import OpenAI
import random
import argparse
import time
import pathlib
import re
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data, save_output

openai_api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('BASE_URL')

industry_list = [
    "Technology",
    "Food & Beverage",
    "E-commerce",
    "Healthcare",
    "Education",
    "Financial Services",
    "Consulting",
    "Real Estate",
    "Renewable Energy",
    "Manufacturing",
    "Transportation",
    "Tourism",
    "Media & Entertainment",
    "Fashion",
    "Agriculture",
    "Retail",
    "Construction",
    "Fitness",
    "Software Development",
    "Professional Services"
]

year_list = [2022, 2023, 2024]
funding_stages = ["Seed", "Series A", "Series B", "Bootstrapped", "Angel Investment"]


def clean_json_response(response_text):
    """Clean the response text to ensure it's valid JSON."""
    print("\n===== CLEANING JSON RESPONSE =====")
    print(f"Response length: {len(response_text)} characters")
    print(f"First 100 chars: {response_text[:100]}")
    print(f"Last 100 chars: {response_text[-100:]}")
    
    # Check if response already has markdown code block format ```json ... ```
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
    if json_match:
        print("Found JSON in markdown code block")
        json_content = json_match.group(1)
    else:
        # First, find the JSON content - extract between outermost braces
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        print(f"JSON bounds: start={start_idx}, end={end_idx}")
        
        if start_idx >= 0 and end_idx > start_idx:
            json_content = response_text[start_idx:end_idx]
        else:
            print("WARNING: Could not find JSON content with braces")
            json_content = ""
    
    # Remove any markdown formatting that might be present
    if not json_content:
        # If no JSON found, return empty dict
        print("WARNING: Empty JSON content, returning empty object")
        return "{}"
    
    print(f"Original JSON content (first 200 chars): {json_content[:200]}...")
    
    # Save original JSON to file for debugging
    debug_dir = "./debug"
    os.makedirs(debug_dir, exist_ok=True)
    with open(f"{debug_dir}/original_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        f.write(json_content)
    
    # Using a simplified approach for cleaning
    
    # 1. Fix unquoted property names - this is a common issue
    json_content = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_content)
    
    # 2. Remove trailing commas in arrays and objects - another common issue
    json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
    
    # 3. Fix missing commas between elements
    json_content = re.sub(r'(["\d])\s*\n\s*"', r'\1,\n"', json_content)
    
    # 4. Convert single quotes to double quotes for property values
    # BUT do this more carefully to avoid issues with apostrophes inside text
    
    # First, normalize single quotes used for properties to double quotes
    # This replaces 'property': with "property":
    json_content = re.sub(r"'(\w+)'\s*:", r'"\1":', json_content)
    
    # Special fix for incomplete JSON: Check if JSON is truncated and complete it
    # This happens when the API returns a partial response
    if not json_content.strip().endswith('}'):
        print("WARNING: JSON appears to be truncated (doesn't end with '}'), attempting to repair...")
        
        # 1. Count opening and closing braces/brackets to see what's missing
        open_braces = json_content.count('{')
        close_braces = json_content.count('}')
        open_brackets = json_content.count('[')
        close_brackets = json_content.count(']')
        
        print(f"Brace balance: {open_braces} opening vs {close_braces} closing")
        print(f"Bracket balance: {open_brackets} opening vs {close_brackets} closing")
        
        # 2. Add missing closing braces and brackets
        missing_braces = open_braces - close_braces
        missing_brackets = open_brackets - close_brackets
        
        if missing_braces > 0 or missing_brackets > 0:
            print(f"Adding {missing_braces} closing braces and {missing_brackets} closing brackets")
            # First close any open brackets
            json_content += ']' * missing_brackets
            # Then close any open braces
            json_content += '}' * missing_braces
            
            # Save the repaired JSON
            with open(f"{debug_dir}/repaired_truncated_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                f.write(json_content)
    
    print(f"Cleaned JSON content (first 200 chars): {json_content[:200]}...")
    
    # Save cleaned JSON to file for debugging
    with open(f"{debug_dir}/cleaned_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        f.write(json_content)
    
    # Debug: Check if the JSON is now valid
    try:
        json.loads(json_content)
        print("JSON is now valid!")
    except json.JSONDecodeError as e:
        print(f"WARNING: JSON is still invalid after cleaning: {e}")
        print(f"Error position: char {e.pos}, line {e.lineno}, column {e.colno}")
        if e.pos < len(json_content):
            # Show more context around the error
            start_pos = max(0, e.pos - 200)
            end_pos = min(len(json_content), e.pos + 200)
            context = json_content[start_pos:end_pos]
            error_pos_in_context = e.pos - start_pos
            marked_context = context[:error_pos_in_context] + " >>> ERROR HERE <<< " + context[error_pos_in_context:]
            print(f"Context around error (400 chars):\n{marked_context}")
            
            # Save the problematic part to a separate file for detailed analysis
            with open(f"{debug_dir}/error_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "w") as f:
                f.write(f"Error: {e}\n")
                f.write(f"Position: char {e.pos}, line {e.lineno}, column {e.colno}\n\n")
                f.write("Context around error:\n")
                f.write(marked_context)
            
            # Check if error mentions delimiter, which is often a comma issue
            if "delimiter" in str(e):
                print("This looks like a missing comma or delimiter issue, trying to fix...")
                # Extract the error position
                error_line = e.lineno
                error_col = e.colno
                error_pos = e.pos
                
                # Add a comma at the error position and try again
                fixed_content = json_content[:error_pos] + "," + json_content[error_pos:]
                with open(f"{debug_dir}/comma_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                    f.write(fixed_content)
                
                try:
                    json_object = json.loads(fixed_content)
                    print("Successfully fixed by adding a comma!")
                    json_content = fixed_content
                except json.JSONDecodeError as comma_error:
                    print(f"Comma fix didn't work: {comma_error}")
            
            # Try a more aggressive but simpler approach - just fix the most basic issues
            # and let JSON.parse handle the rest as it can be more forgiving
            try:
                # Directly convert to a Python object and back to JSON
                # This may work for cases where the JSON is nearly valid
                from ast import literal_eval
                
                # Only try this if it looks mostly like valid Python dict syntax
                if json_content.strip().startswith('{') and json_content.strip().endswith('}'):
                    print("Attempting direct Python object conversion...")
                    # Replace problematic apostrophes in text with spaces to avoid parsing errors
                    safer_content = re.sub(r'(\w)"(\w)', r'\1 \2', json_content)
                    safer_content = re.sub(r'(\w)\'(\w)', r'\1 \2', safer_content)
                    
                    # Save the safer content for inspection
                    with open(f"{debug_dir}/safer_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                        f.write(safer_content)
                    
                    # Try to evaluate as Python dictionary and convert back to JSON
                    try:
                        # Use a more direct approach with json.loads after minimal cleaning
                        minimal_clean = json_content
                        # Double quote all single-quoted strings that look like JSON properties
                        minimal_clean = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', minimal_clean)
                        # Convert remaining single quotes to double quotes
                        minimal_clean = minimal_clean.replace("'", '"')
                        
                        # Save minimal cleaned version
                        with open(f"{debug_dir}/minimal_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                            f.write(minimal_clean)
                        
                        # Try parsing now
                        json_object = json.loads(minimal_clean)
                        json_content = json.dumps(json_object)
                        print("Successfully converted using minimal cleaning!")
                        
                        # Also save the successful version
                        with open(f"{debug_dir}/successful_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                            f.write(json_content)
                    except Exception as parsing_error:
                        print(f"Direct conversion failed: {parsing_error}")
            except Exception as advanced_error:
                print(f"Advanced conversion attempt failed: {advanced_error}")

    return json_content


def generate_business_plan(
    model_name="gpt-3.5-turbo",
    industry="Technology",
    data_for_complete=None
):
    print(f"\n===== GENERATING BUSINESS PLAN FOR {industry} =====")
    time.sleep(random.random() * 1.5)
    
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
        print(f"Using custom base URL: {base_url}")
    else:
        client = OpenAI(api_key=openai_api_key)
        print("Using default OpenAI base URL")
    
    system_prompt = """You are an expert business consultant who specializes in developing comprehensive business plans.
Your task is to generate a detailed business plan following a specific schema.

EXTREMELY IMPORTANT OUTPUT FORMAT INSTRUCTIONS:
1. Return ONLY a valid JSON object with no additional text or markdown formatting
2. Do NOT use ```json code blocks or any other wrappers
3. Ensure all property names use double quotes (e.g., "property": not 'property':)
4. Do not include trailing commas in arrays or objects
5. For apostrophes in text (like "company's" or "it's"), use a regular apostrophe ('), NOT escaped quotes
6. Keep your JSON structure simple - don't nest objects too deeply
7. Do not include any explanatory text before or after the JSON object
8. The response should start with { and end with } - nothing else

Example of correct formatting:
{
  "company_name": "Tech Solutions Inc.",
  "industry": "Technology",
  "executive_summary": {
    "mission_statement": "Our company's mission is to innovate."
  }
}"""
    
    user_prompt = """Below is a structured schema that you need to use as a guide to create a very detailed and comprehensive business plan for a company.

- Industry of the company: {industry}
- The schema provides the structure for the business plan. Please fill in all fields with realistic, specific, and detailed content.
- Create a compelling company name, business concept, and mission statement.
- Include detailed market analysis with industry trends and target market segments.
- Provide specific products/services with clear features and benefits.
- Develop a comprehensive marketing strategy.
- Include detailed operational plans and financial projections.
- The financial projections should include realistic revenue models, funding requirements, and projected P&L.
- Include thorough risk assessment and mitigation strategies.
- Make all content extremely detailed, specific, and realistic.

STRICT JSON FORMAT REQUIREMENTS:
1. Your entire response must be ONLY a valid JSON object, nothing else
2. All property names must be in double quotes
3. No trailing commas in objects or arrays
4. Keep apostrophes as simple apostrophes in text, not escaped quotes
5. Do not include any explanatory text, comments, or markdown formatting
6. Do not wrap your response in ```json or any other formatting

Follow the exact schema structure in the JSON template below:

""".format(industry=industry)
    
    data_json = json.dumps(data_for_complete, ensure_ascii=False, indent=1)
    user_prompt += data_json
    
    print(f"Schema data length: {len(data_json)} characters")
    print(f"Total prompt length: {len(system_prompt) + len(user_prompt)} characters")

    # No retries, just one attempt for debugging
    print("\nMaking a single API call (no retries)...")
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,  # Reduced temperature for more precise formatting
            response_format={"type": "json_object"}  # Use JSON response format if supported
        ).choices[0].message.content
        
        print(f"Received response of length: {len(response)} characters")
        
        # Clean the JSON response to handle common formatting issues
        clean_json = clean_json_response(response)
        
        try:
            print("Attempting to parse JSON...")
            parsed_response = json.loads(clean_json)
            print("Successfully parsed JSON response!")
            
            # Add industry field to the response
            parsed_response["industry"] = industry
            print(f"Added industry field: {industry}")
            
            # Print some basic info about the parsed response
            print(f"Response contains {len(parsed_response.keys())} top-level keys")
            if "company_name" in parsed_response:
                print(f"Company name: {parsed_response['company_name']}")
            
            return parsed_response
            
        except json.JSONDecodeError as je:
            print(f"JSON parsing error after cleaning: {je}")
            print(f"Error at line {je.lineno}, column {je.colno}, position {je.pos}")
            if je.pos < len(clean_json):
                error_context = clean_json[max(0, je.pos-30):min(len(clean_json), je.pos+30)]
                print(f"Context around error: ...{error_context}...")
            
            # Return minimal response since we're not retrying
            minimal_response = {
                "company_name": f"{industry} Example Company",
                "industry": industry,
                "executive_summary": {
                    "mission_statement": "Creating value in the " + industry + " sector."
                }
            }
            print(f"Returning minimal response due to JSON error: {json.dumps(minimal_response, indent=2)}")
            return minimal_response
            
    except Exception as e:
        print(f"API or other error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Return minimal response since we're not retrying
        minimal_response = {
            "company_name": f"{industry} Example Company",
            "industry": industry,
            "executive_summary": {
                "mission_statement": "Creating value in the " + industry + " sector."
            }
        }
        print(f"Returning minimal response due to API error: {json.dumps(minimal_response, indent=2)}")
        return minimal_response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default='gpt-3.5-turbo')
    parser.add_argument("--industry", type=str, default="Technology")
    parser.add_argument("--data_for_complete", type=str, required=True)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument("--json_idx", type=int, default=0)
    args = parser.parse_args()
    
    print("\n===== BUSINESS PLAN GENERATOR =====")
    print(f"Model: {args.model_name}")
    print(f"Industry: {args.industry}")
    print(f"Data file: {args.data_for_complete}")
    print(f"Output directory: {args.output_dir}")
    
    try:
        model_name = args.model_name
        print(f"Loading schema data from {args.data_for_complete}...")
        data_for_complete = load_json_data(args.data_for_complete)
        print(f"Schema data loaded successfully, contains {len(json.dumps(data_for_complete))} characters")
        
        field_name = args.data_for_complete.split("/")[-1].split(".")[0]
        print(f"Field name: {field_name}")

        industry = args.industry
        print(f"Generating business plan for {industry}...")
        response = generate_business_plan(
            model_name, industry, data_for_complete
        )
        
        output_dir = args.output_dir if args.output_dir else f"./output/business-plan/en/config"
        print(f"Saving output to {output_dir}...")
        save_output(output_dir, response, industry.replace(' ', '_'), args.json_idx, field_name, "json")
        print("Business plan generated and saved successfully!")
        
    except Exception as e:
        print(f"\n===== ERROR IN MAIN FUNCTION =====")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main() 