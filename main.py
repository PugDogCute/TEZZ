import random
import json
import time
from openai import OpenAI, APIError


OPENAI_API_KEY = "Insert your API key, follow this link to get one: https://platform.openai.com/api-keys. Please follow the quick start section to get the best instruction"
client = OpenAI()

def generate_quiz(file):
    quiz = []
    try:
        with open(file, 'r') as f:
            for i, line in enumerate(f, start=1):
                parts = line.split('|')
                if len(parts) != 2:
                    continue
                question, answer = map(str.strip, parts)
                incorrect_answer = generate_incorrect_choices(question)
                multiple_answer = [answer] + incorrect_answer
                random.shuffle(multiple_answer)

                quiz.append({
                    "question": f"{i}. {question}",
                    "answer": answer,
                    "choices": multiple_answer
                })
    except FileNotFoundError:
        print(f"File {file} not found, please try again with it's path")
        return None
    return quiz

def convert_to_string(s): 
    new = "" 
    for x in s: 
        new += x 
    return new 

def convert_to_dict(s):
    return json.loads(s)

def delete_white_lines(file):
    with open(file, 'r') as f:
        lines = f.readlines()

    non_blank_lines = [line for line in lines if line.strip()]

    with open(file, 'w') as f:
        f.writelines(non_blank_lines)

    return file
def generate_incorrect_choices(question):
    user_demand = """Do not include any explanations, only provide a  RFC8259 compliant JSON response  following this format without deviation.
    [{
    "ans_1": "the first answer",
    "ans_2": "the second answer",
    "ans_3": "the third answer",
    "ans_4": "the fourth answer"
    }]"""

    response = None
    while response is None or (isinstance(response, dict) and response.get('error', {}).get('code') == 'rate_limit_exceeded'):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": f"create me 4 more incorrect answers for this question: {question}.{user_demand}"}
                ]
            )
        except APIError as e:
            if e.code == 'rate_limit_exceeded':
                print("Hold up, we are generating the quiz for you. Waiting for 20 seconds...")
                time.sleep(20)
                continue
            else:
                raise


    ans_dict = convert_to_dict(convert_to_string(response.choices[0].message.content))
    ans_list = []
    for i in ans_dict.values():
        ans_list.append(i)
    return ans_list

if __name__ == "__main__":
    file_path = delete_white_lines(input("What is your .txt file path: "))
    quizzes = generate_quiz(file_path)

    if quizzes:
        score = 0
        max_quiz_num = len(quizzes)
        min_quiz_num = 1
        
        while True:
            try:
                quiz_num = int(input(f"How many question do you want to do? (from {min_quiz_num} to {max_quiz_num} questions): "))
                if min_quiz_num <= quiz_num and quiz_num <= max_quiz_num:
                    print("Let's go")
                    break
                else:
                    print("Please try entering a proper number")
            except ValueError:
                print("Please enter a valid integer number")

        for question in quizzes[:quiz_num]:
            print(question["question"])
            for i, choice in enumerate(question["choices"], start=1):
                print(f"{chr(64 + i)}. {choice}")

            user_ans = input("(Type 'quit' to quit the quiz test) What is your answer: ").strip()
            if user_ans.lower() == "quit":
                print(f"Your score is {score}/{quiz_num} or ", score/quiz_num*100, "%")
                break

            correct_index = question["choices"].index(question["answer"]) + 1
            if user_ans.lower() == question["answer"].lower() or user_ans.upper() == chr(64 + correct_index):
                print("Correct")
                score += 1
            else:
                print(f"Incorrect, the correct answer is: {question['answer']}")
        print(f"Your score is {score}/{quiz_num} or ", score/quiz_num*100, "%")
