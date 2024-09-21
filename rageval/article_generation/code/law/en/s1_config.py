import os
import json
import sys
from openai import OpenAI
import random
import argparse
import time
import pathlib
from datetime import datetime
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


def generate_article(
    model_name,
    data_for_complete,
    crime_name,
    crime_detail,
):
    time.sleep(random.random() * 1.5)
    system_prompt = 'You are an experienced court clerk, you have rich experience in writing legal documents, and have a strong imagination.'
    user_prompt = f"""You need to write a detailed legal document sample.
You need to write a legal document item based on a JSON template:
- The charge to be written is: {crime_name}
- In the "defendant" field, the defendant's name, gender, and birth date have been filled out. You only need to fill in their ethnicity, occupation, etc.
- In the "defenseLawyer" field, the lawyer's name has been filled out. You only need to fill in the law firm they belong to.
- In the "caseProcess" field, please provide specific dates and detailed descriptions for each key event.
- In the "criminalFacts" field, please create a scenario involving {crime_name}, including specific behavior, time period, place, and amounts involved.
- The "Details" field in "criminalFacts" is a list and should have 3 to 4 incidents, each with "timePeriod", "behavior", and "evidence" elements.
- The offender's specific actions should be very detailed. You need to carefully supplement the case history and details, possibly involving amounts, times, places, brands, etc., that should look very real.
- Evidence materials supporting the verdict need to be very detailed, and you can list multiple pieces of evidence, including written evidence, physical evidence, witness testimony, etc.
- The "legalProcedure" field includes the trial date, trial result, and specific sentencing (if probation is applicable, also inform the probation period).
{crime_detail}
"""
    user_prompt += json.dumps(data_for_complete, ensure_ascii=False, indent=1)
    if base_url != '':
        client = OpenAI(api_key=openai_api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=openai_api_key)
    while True:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            ).choices[0].message.content
            response = response[response.find("{") : response.rfind("}") + 1]
            response = json.loads(response)
            break
        except Exception as e:
            print(f"Error occurred: {e}. Retrying...")
            time.sleep(1)
    return response
    

def set_value(data):
    city = random.choice(names)
    while True:
        street = random.choice(names)
        if street != city:
            break
    address = f"{random.randint(1, 100)}, {street} street, {city}"
    while True:
        district = random.choice(names)
        if district != city and district != street:
            break
    court = f"{district}, {city}, Court"
    procuratorate = f"{district}, {city}, Procuratorate"
    def get_name():
        return random.choice(characters) + '. ' + random.choice(surnames)
    data["courtAndProcuratorate"]["court"] = court
    data["courtAndProcuratorate"]["procuratorate"] = procuratorate
    data["defendant"]["name"] = get_name()
    data["defendant"]["gender"] = random.choice(["male", "female"])
    day = random.randint(1, 28)
    if day == 1:
        day = "1st"
    elif day == 2:
        day = "2nd"
    elif day == 3:
        day = "3rd"
    else:
        day = f"{day}th"
    data["defendant"]["birthdate"] = f"{day}, {random.choice(month_list)}, {random.randint(1960, 2000)}"
    data["defendant"]["residence"] = address
    data["defenseLawyer"]["name"] = get_name()
    data["chiefJudge"] = get_name()
    data["judge"] = get_name()
    data["clerk"] = get_name()
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="single")
    parser.add_argument("--model_name", type=str, default='gpt-4o')
    parser.add_argument("--data_for_complete", type=str, default=None)
    parser.add_argument("--crime_names", type=str, default=None)
    parser.add_argument("--crime_name_idx", type=int, default=None)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument("--json_idx", type=int, default=0)
    args = parser.parse_args()

    json_idx = args.json_idx
    model_name = args.model_name

    data = load_json_data(args.data_for_complete)

    data = set_value(data)


    crime_dict_list = load_json_data(args.crime_names)
    crime_dict = crime_dict_list[args.crime_name_idx]
    crime_name, crime_detail = crime_dict['name'], crime_dict['details']
    response = generate_article(model_name, data, crime_name, crime_detail)
    save_output(args.output_dir, response, crime_name, json_idx, None, "json")

if __name__ == "__main__":
    main()
