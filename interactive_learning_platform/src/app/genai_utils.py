import os
import json
from flask import current_app

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

def get_openai_client():
    """Initializes and returns the OpenAI client."""
    # The API key is available in the environment variable OPENAI_API_KEY
    # The client will automatically pick it up.
    return OpenAI()

def generate_activity_draft(topic_or_content, activity_type):
    """
    Uses GenAI to generate a draft for a learning activity.
    
    Args:
        topic_or_content (str): The subject matter or content to base the activity on.
        activity_type (str): The type of activity (e.g., 'quiz', 'poll', 'short_answer').
        
    Returns:
        dict: A dictionary containing the generated activity content (title, question, options, etc.)
              or None if generation fails.
    """
    if not OPENAI_AVAILABLE:
        print("OpenAI is not available. GenAI features are disabled.")
        return None
    
    client = get_openai_client()
    model = current_app.config['GENAI_MODEL']
    
    # Define the desired JSON output structure
    if activity_type == 'quiz':
        json_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "A concise title for the quiz."},
                "question": {"type": "string", "description": "The quiz question."},
                "options": {"type": "array", "items": {"type": "string"}, "description": "A list of 4 multiple-choice options."},
                "correct_answer": {"type": "string", "description": "The exact text of the correct option."}
            },
            "required": ["title", "question", "options", "correct_answer"]
        }
        prompt_suffix = "Generate a multiple-choice quiz question with 4 options and the correct answer based on the following content. The output MUST be a JSON object conforming to the provided schema."
    elif activity_type == 'short_answer':
        json_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "A concise title for the short answer activity."},
                "question": {"type": "string", "description": "The short answer question."}
            },
            "required": ["title", "question"]
        }
        prompt_suffix = "Generate a thought-provoking short answer question based on the following content. The output MUST be a JSON object conforming to the provided schema."
    else:
        # For 'poll' or 'word_cloud', we can use a simpler structure or just a question
        return None # Simplified for initial implementation

    system_message = f"You are an expert educational content generator. Your task is to create a learning activity of type '{activity_type}'. {prompt_suffix}"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Content/Topic: {topic_or_content}"}
            ],
            response_format={"type": "json_object", "schema": json_schema}
        )
        
        # The response text should be a JSON string
        raw_json = response.choices[0].message.content
        return json.loads(raw_json)
        
    except Exception as e:
        print(f"GenAI activity generation failed: {e}")
        return None

def group_short_answers(answers):
    """
    Uses GenAI to group similar short answers from students.
    
    Args:
        answers (list): A list of student answer strings.
        
    Returns:
        dict: A dictionary where keys are group labels and values are lists of answer indices.
              Example: {"Group A (Concept X)": [0, 2], "Group B (Concept Y)": [1, 3]}
    """
    if not OPENAI_AVAILABLE:
        print("OpenAI is not available. GenAI features are disabled.")
        return None
    
    client = get_openai_client()
    model = current_app.config['GENAI_MODEL']
    
    # Prepend index to each answer for easy mapping back
    indexed_answers = [f"[{i}]: {answer}" for i, answer in enumerate(answers)]
    answers_text = "\n".join(indexed_answers)
    
    json_schema = {
        "type": "object",
        "patternProperties": {
            "^.*$": {
                "type": "array",
                "items": {"type": "integer", "description": "The index of the answer in the input list."}
            }
        },
        "description": "A mapping of group labels to a list of answer indices. The group labels should be descriptive summaries of the common theme in the answers."
    }
    
    system_message = "You are an expert in qualitative data analysis. Your task is to group the following short answers into a few thematic categories. The output MUST be a JSON object conforming to the provided schema. The keys should be descriptive group labels, and the values should be lists of the original answer indices (the number in the square brackets)."
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Short answers to group:\n{answers_text}"}
            ],
            response_format={"type": "json_object", "schema": json_schema}
        )
        
        raw_json = response.choices[0].message.content
        return json.loads(raw_json)
        
    except Exception as e:
        print(f"GenAI answer grouping failed: {e}")
        return None

