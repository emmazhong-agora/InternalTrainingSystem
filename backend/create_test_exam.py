#!/usr/bin/env python3
"""
Script to create a test exam with sample questions.
Run this after starting the backend server.

Usage:
    python3 create_test_exam.py [username] [password]

If no credentials provided, you'll be prompted to enter them.
"""

import requests
import sys
import json
import getpass

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def login(username="admin", password="admin123"):
    """Login and get access token."""
    print(f"Logging in as {username}...")

    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "username": username,
            "password": password
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful! User: {data['user']['username']}")
        return data['access_token']
    else:
        print(f"✗ Login failed: {response.text}")
        sys.exit(1)

def create_exam(token):
    """Create a test exam."""
    print("\nCreating test exam...")

    exam_data = {
        "title": "Python Fundamentals Quiz",
        "description": "Test your knowledge of Python basics including variables, data types, control flow, and functions.",
        "time_limit_minutes": 30,
        "pass_threshold_percentage": 70.0,
        "max_attempts": 3,
        "status": "published",
        "show_correct_answers": True,
        "randomize_questions": False,
        "randomize_options": False,
        "video_ids": []
    }

    response = requests.post(
        f"{API_BASE_URL}/exams/",
        headers={"Authorization": f"Bearer {token}"},
        json=exam_data
    )

    if response.status_code == 201:
        exam = response.json()
        print(f"✓ Exam created! ID: {exam['id']}, Title: {exam['title']}")
        return exam['id']
    else:
        print(f"✗ Failed to create exam: {response.text}")
        sys.exit(1)

def add_questions(token, exam_id):
    """Add sample questions to the exam."""
    print(f"\nAdding questions to exam {exam_id}...")

    questions = [
        {
            "question_type": "multiple_choice",
            "question_text": "What is the output of print(type([]))?",
            "points": 1.0,
            "options": [
                "<class 'list'>",
                "<class 'dict'>",
                "<class 'tuple'>",
                "<class 'set'>"
            ],
            "correct_answer": "0",
            "explanation": "The type() function returns the type of an object. An empty [] creates a list, so type([]) returns <class 'list'>.",
            "sort_order": 0
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Which of the following is a mutable data type in Python?",
            "points": 1.0,
            "options": [
                "tuple",
                "string",
                "list",
                "integer"
            ],
            "correct_answer": "2",
            "explanation": "Lists are mutable, meaning their elements can be changed after creation. Tuples, strings, and integers are immutable.",
            "sort_order": 1
        },
        {
            "question_type": "true_false",
            "question_text": "Python is a statically-typed language.",
            "points": 1.0,
            "correct_answer": "false",
            "explanation": "Python is a dynamically-typed language, meaning you don't need to declare variable types explicitly.",
            "sort_order": 2
        },
        {
            "question_type": "multiple_choice",
            "question_text": "What does the 'def' keyword do in Python?",
            "points": 1.0,
            "options": [
                "Defines a variable",
                "Defines a function",
                "Defines a class",
                "Defines a loop"
            ],
            "correct_answer": "1",
            "explanation": "The 'def' keyword is used to define a function in Python.",
            "sort_order": 3
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Which operator is used for floor division in Python?",
            "points": 1.0,
            "options": [
                "/",
                "//",
                "%",
                "**"
            ],
            "correct_answer": "1",
            "explanation": "The // operator performs floor division, which returns the largest integer less than or equal to the division result.",
            "sort_order": 4
        },
        {
            "question_type": "true_false",
            "question_text": "Python uses indentation to define code blocks.",
            "points": 1.0,
            "correct_answer": "true",
            "explanation": "Unlike many other languages that use braces {}, Python uses indentation to define code blocks.",
            "sort_order": 5
        },
        {
            "question_type": "multiple_choice",
            "question_text": "What is the correct way to create a dictionary in Python?",
            "points": 1.0,
            "options": [
                "dict = []",
                "dict = ()",
                "dict = {}",
                "dict = <>"
            ],
            "correct_answer": "2",
            "explanation": "Dictionaries in Python are created using curly braces {} with key-value pairs.",
            "sort_order": 6
        },
        {
            "question_type": "true_false",
            "question_text": "Lists in Python can contain elements of different data types.",
            "points": 1.0,
            "correct_answer": "true",
            "explanation": "Python lists are heterogeneous, meaning they can contain elements of different types (e.g., integers, strings, objects).",
            "sort_order": 7
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Which method is used to add an element to the end of a list?",
            "points": 1.0,
            "options": [
                "add()",
                "append()",
                "insert()",
                "extend()"
            ],
            "correct_answer": "1",
            "explanation": "The append() method adds a single element to the end of a list.",
            "sort_order": 8
        },
        {
            "question_type": "multiple_choice",
            "question_text": "What is the output of: print(3 ** 2)?",
            "points": 1.0,
            "options": [
                "6",
                "9",
                "8",
                "32"
            ],
            "correct_answer": "1",
            "explanation": "The ** operator is the exponentiation operator in Python. 3 ** 2 means 3 raised to the power of 2, which equals 9.",
            "sort_order": 9
        }
    ]

    response = requests.post(
        f"{API_BASE_URL}/exams/{exam_id}/add-generated-questions",
        headers={"Authorization": f"Bearer {token}"},
        json=questions
    )

    if response.status_code == 200:
        exam = response.json()
        print(f"✓ Added {len(questions)} questions to exam!")
        print(f"  Total questions: {exam['question_count']}")
        print(f"  Total points: {exam['total_points']}")
        return exam
    else:
        print(f"✗ Failed to add questions: {response.text}")
        sys.exit(1)

def get_exam_info(token, exam_id):
    """Get exam information."""
    print(f"\nFetching exam info...")

    response = requests.get(
        f"{API_BASE_URL}/exams/{exam_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        exam = response.json()
        return exam
    else:
        print(f"✗ Failed to get exam info: {response.text}")
        return None

def main():
    print("=" * 60)
    print("Creating Test Exam with Sample Questions")
    print("=" * 60)

    # Get credentials
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        print("\nPlease enter your admin credentials:")
        username = input("Username: ").strip() or "admin"
        password = getpass.getpass("Password: ").strip() or "admin123"

    # Login
    token = login(username, password)

    # Create exam
    exam_id = create_exam(token)

    # Add questions
    exam = add_questions(token, exam_id)

    # Display summary
    print("\n" + "=" * 60)
    print("EXAM CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\nExam ID: {exam_id}")
    print(f"Title: {exam['title']}")
    print(f"Status: {exam['status']}")
    print(f"Questions: {exam['question_count']}")
    print(f"Total Points: {exam['total_points']}")
    print(f"Pass Threshold: {exam['pass_threshold_percentage']}%")
    print(f"Time Limit: {exam.get('time_limit_minutes', 'Unlimited')} minutes")

    print("\n" + "-" * 60)
    print("HOW TO ACCESS THE EXAM:")
    print("-" * 60)
    print(f"\n1. Admin View (Edit/Results):")
    print(f"   http://localhost:5173/admin/exams/{exam_id}/edit")
    print(f"   http://localhost:5173/admin/exams/{exam_id}/results")

    print(f"\n2. Public Exam Taking (No login required):")
    print(f"   http://localhost:5173/exam/{exam_id}")
    print(f"   Note: Email must match a registered user account")

    print(f"\n3. API Endpoints:")
    print(f"   GET  {API_BASE_URL}/exams/public/{exam_id}")
    print(f"   POST {API_BASE_URL}/exams/public/start")
    print(f"   POST {API_BASE_URL}/exams/public/submit/{{attempt_id}}")

    print("\n" + "=" * 60)
    print("Share the public URL with participants to take the exam!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
