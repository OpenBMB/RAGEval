import os
import json
import random
import argparse
import time
import sys
import pathlib
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(root_dir)

from utils import load_json_data, save_output

openai_api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('BASE_URL')
names = [
    'Springfield', 'Riverton', 'Clearwater', 'Sunnyvale', 'Greenfield', 'Fairview',
    'Hillcrest', 'Brookside', 'Lakewood', 'Cedarwood', 'Ridgewood', 'Roseville',
    'Maplewood', 'Pinehurst', 'Oakwood', 'Brighton', 'Kingsport', 'Lancaster',
    'Georgetown', 'Huntington', 'Madison', 'Norwood', 'Summerville', 'Windsor',
    'Ashton', 'Belmont', 'Cameron', 'Danbury', 'Eastwood', 'Foxboro', 'Granville',
    'Hartford', 'Inglewood', 'Jacksonville', 'Kensington', 'Lexington', 'Milton',
    'Newport', 'Orchard', 'Preston', 'Quincy', 'Richmond', 'Sterling', 'Tiverton',
    'Unionville', 'Vermont', 'Westwood', 'Yorktown', 'Ashland', 'Bridgewater',
    'Clarksville', 'Dunmore', 'Elmwood', 'Farmington', 'Greenville', 'Harrison',
    'Irvington', 'Jefferson', 'Kingston', 'Lakeside', 'Mayfield', 'Newton',
    'Oxford', 'Princeton', 'Quailwood', 'Rockford', 'Southport', 'Trenton',
    'Upton', 'Victoria', 'Wilton', 'Yorkshire', 'Arlington', 'Bayside', 'Charleston',
    'Dover', 'Eagleton', 'Franklin', 'Glenwood', 'Hamilton', 'Indianola',
    'Jamestown', 'Knoxville', 'Linden', 'Manchester', 'Northwood', 'Oakland',
    'Parker', 'Quarryville', 'Riverside', 'Seaside', 'Tremont', 'Urbana',
    'Vandalia', 'Woodland', 'Yarmouth', 'Zephyrhills'
]
surnames = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 
    'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 
    'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 
    'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 
    'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King', 
    'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores', 'Green', 
    'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 
    'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 
    'Parker', 'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 
    'Morales', 'Murphy', 'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 
    'Cooper', 'Peterson', 'Bailey', 'Reed', 'Kelly', 'Howard', 'Ramos', 
    'Kim', 'Cox', 'Ward', 'Richardson', 'Watson', 'Brooks', 'Chavez', 
    'Wood', 'James', 'Bennett', 'Gray', 'Mendoza', 'Ruiz', 'Hughes', 
    'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel', 'Myers', 'Long', 
    'Ross', 'Foster', 'Jimenez'
]

characters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

month_list = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

may_died = ['Bacterial Food Poisoning', 'Hepatitis A', 'Malaria', 'Nasopharyngeal Malignancy', 'Esophageal Malignancy', 
            'Epidemic Cerebrospinal Meningitis', 'Pneumonia', 'Congenital Heart Disease', 'Neonatal Tetanus']

def generate_article(
    model_name, 
    disease_name,
    disease_detail,
    data_for_complete,
    is_surgery, 
    is_dead
):
    time.sleep(random.random() * 1.5)
    system_prompt = 'You are an experienced attending physician, you have extensive experience in writing hospitalization record, and you have a strong imagination.'
    user_prompt = f"""You are writing a medical record for a patient.
You need to write a hospital record example based on a template file:
- The disease to be written this time is: {disease_name}-{disease_detail}
- Note: The patient {'had surgery' if is_surgery else 'did not have surgery'}, {'is deceased' if is_dead else 'is not deceased'}
- Reply directly in JSON format, no other sentences.
- Fill in every field, not just an example, such as Senior Physician Rounds Records, Handover Records, Transfer Records, Stage Summary, Medical Orders, Temperature Chart and Auxiliary Examination Reports, etc.
- Some basic information of the patient such as name, gender, age, address, admission time, etc. has been filled out.
- The hospital should be in the same city as the patient's address.
Template as follows:
"""
    user_prompt += json.dumps(data_for_complete, ensure_ascii=False, indent=1)
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    while True:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        ).choices[0].message.content
        response = response[response.find("{") : response.rfind("}") + 1]
        try:
            response = json.loads(response)
            break
        except json.JSONDecodeError:
            print("JSONDecodeError")
            continue
    return response


def set_value(schema, disease_name, disease_detail):
    def get_name():
        return random.choice(characters) + '. ' + random.choice(surnames)
    schema['Hospitalization Record']['Basic Information']['Name'] = get_name()
    schema['Hospitalization Record']['Basic Information']['Gender'] = random.choice(["male", "female"])
    if disease_name=="Pregnancy, Childbirth, and the Puerperium Complications":
        schema['Hospitalization Record']['Basic Information']['Gender'] = "female"
    if schema['Hospitalization Record']['Basic Information']['Gender'] == "male":
        del schema['Hospitalization Record']["Marital and Family History"]["Menstrual History"]

    if disease_detail['Name'] in may_died:
        is_dead = random.random() > 0.8
    else:
        is_dead = False
    is_surgery = random.random() > 0.8

    if not is_dead:
        del schema['Hospitalization Record']['Post-Admission Course Records']['Death Related']
    else:
        is_surgery = True
    if not is_surgery:
        del schema['Hospitalization Record']['Post-Admission Course Records']['Surgery Related']
    schema['Hospitalization Record']['Basic Information']['Age'] = f"{random.randint(1, 100)}"
    if disease_name == "Conditions Originating in the Perinatal Period":
        schema['Hospitalization Record']['Basic Information']['Age'] = f"{random.randint(1, 10)} hours after birth"
    day = random.randint(1, 28)
    if day == 1:
        day = "1st"
    elif day == 2:
        day = "2nd"
    elif day == 3:
        day = "3rd"
    else:
        day = f"{day}th"
    schema['Hospitalization Record']['Basic Information']['Admission Time'] = f"{day}, {random.choice(month_list)}"
    city = random.choice(names)
    while True:
        street = random.choice(names)
        if street != city:
            break
    address = f"{random.randint(1, 100)}, {street} street, {city}"
    schema['Hospitalization Record']['Basic Information']['Address'] = address
    return schema, is_surgery, is_dead


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="new")
    parser.add_argument("--model_name", type=str, default='gpt-4o')
    parser.add_argument("--data_for_complete", type=str, required=True)
    parser.add_argument("--data_for_reference", type=str, default=None)
    parser.add_argument("--ref_idx", type=int, default=0)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument("--json_idx", type=int, default=0)
    args = parser.parse_args()

    data = load_json_data(args.data_for_reference)
    model_name = args.model_name
    
    disease_type, disease_detail = list(data.items())[args.ref_idx]

    for disease_item in disease_detail:
        schema = load_json_data(args.data_for_complete)
        
        schema, is_surgery, is_dead = set_value(schema, disease_type, disease_item)
        response = generate_article(model_name, disease_type, disease_item, schema, is_surgery, is_dead)
        response['DiseaseType'] = {disease_type: disease_item}
        save_output(args.output_dir, response, disease_type, args.json_idx, disease_item['Name'], "json")


if __name__ == "__main__":
    main()
