import sys
import os
import json
import random
import argparse
import time
import pathlib
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

openai_api_key = os.getenv("OPENAI_API_KEY")
load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)


PROMPT_TEMPLATE="""You are a schema generation model tasked with creating a JSON schema for the domain of {domain}. You will be provided with one or more seed documents to guide your understanding of common patterns and fields within this domain. The schema should summarize key, universally applicable fields relevant to this domain, ensuring that it captures the most important and common configurations. This schema will be used as a blueprint for generating random configurations (configs), which will later guide the creation of {article_type}.

Key requirements:

	1.	Comprehensive and Universal: The schema must encapsulate fields that are broadly applicable to {domain}. Avoid overly specific or niche details unless they are critical to understanding the domain. Refer to the provided seed documents to identify common fields or patterns.
	2.	Structured and Descriptive: Each field should have:
	•	Description: Explaining the purpose of the field.
	•	Data Type: Defining the field as, for example, string, integer, boolean, etc.
	•	Optional/Required: Whether this field is mandatory or optional.
	3.	Reference Seed Documents: Analyze the structure and content of the provided seed documents to extract commonalities. Use these as a basis to create a schema that generalizes across the domain while maintaining flexibility.
	4.	Random Config Generation: The schema should support the generation of diverse configs, ensuring that each config will make sense within the {domain} context and allow for meaningful variations.
	5.	Content Creation Support: The schema will inform the creation of {article_type} in {domain}. Include fields that could impact content structure, such as:
	•	Themes
	•	Tone/Style
	•	Content Structure
	•	Key Elements
	6.	Flexibility and Modularity: The schema should allow for extension and adaptation, so future fields or sub-domains can be added as needed."""

domain = input("What is the domain of the schema? ")
article_type = input("What is the expected generated article type? ")

prompt = PROMPT_TEMPLATE.format(domain=domain, article_type=article_type)
print(prompt)