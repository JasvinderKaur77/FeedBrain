from google import genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def summarise_content(title: str, content: str, source_type: str) -> dict:
    if not content or len(content.strip()) < 50:
        return {
            "summary": ["Content too short to summarise", "Try adding a note manually", "Check if the URL is accessible"],
            "tags": ["uncategorised"]
        }

    prompt = f"""You are FeedBrain, an AI that helps people remember what they consume.

Analyse this {source_type} content and return a JSON response with exactly this structure:
{{
    "summary": ["bullet point 1", "bullet point 2", "bullet point 3"],
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Rules:
- summary: exactly 3 bullet points, each one sentence, capturing the most important insights
- tags: 3-5 lowercase tags describing the topic/domain
- Be specific and insightful, not generic
- Return ONLY the JSON, no other text, no markdown backticks

Title: {title}

Content:
{content[:6000]}"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        response_text = response.text.strip()

        # Clean markdown backticks if Gemini adds them
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()

        parsed = json.loads(response_text)

        return {
            "summary": parsed.get("summary", ["Could not generate summary"]),
            "tags": parsed.get("tags", ["uncategorised"])
        }

    except json.JSONDecodeError:
        return {
            "summary": ["Content saved successfully", "Summary generation failed", "Raw content is stored"],
            "tags": ["uncategorised"]
        }
    except Exception as e:
        return {
            "summary": ["Content saved successfully", f"Error: {str(e)}", "Raw content is stored"],
            "tags": ["uncategorised"]
        }

# import anthropic
# import json
# import os
# from dotenv import load_dotenv

# load_dotenv()

# client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# def summarise_content(title: str, content: str, source_type: str) -> dict:
#     if not content or len(content.strip()) < 50:
#         return {
#             "summary": ["Content too short to summarise", "Try adding a note manually", "Check if the URL is accessible"],
#             "tags": ["uncategorised"]
#         }
    
#     prompt = f"""You are FeedBrain, an AI that helps people remember what they consume.

# Analyse this {source_type} content and return a JSON response with exactly this structure:
# {{
#     "summary": ["bullet point 1", "bullet point 2", "bullet point 3"],
#     "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
# }}

# Rules:
# - summary: exactly 3 bullet points, each one sentence, capturing the most important insights
# - tags: 3-5 lowercase tags describing the topic/domain
# - Be specific and insightful, not generic
# - Return ONLY the JSON, no other text

# Title: {title}

# Content:
# {content[:6000]}"""

#     try:
#         message = client.messages.create(
#             model="claude-haiku-4-5",
#             max_tokens=500,
#             messages=[
#                 {"role": "user", "content": prompt}
#             ]
#         )
        
#         response_text = message.content[0].text.strip()
        
#         parsed = json.loads(response_text)
        
#         return {
#             "summary": parsed.get("summary", ["Could not generate summary"]),
#             "tags": parsed.get("tags", ["uncategorised"])
#         }
        
#     except json.JSONDecodeError:
#         return {
#             "summary": ["Content saved successfully", "Summary generation failed", "Raw content is stored"],
#             "tags": ["uncategorised"]
#         }
#     except Exception as e:
#         return {
#             "summary": ["Content saved successfully", f"Error: {str(e)}", "Raw content is stored"],
#             "tags": ["uncategorised"]
#         }