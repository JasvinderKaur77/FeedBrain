from services.extractor import extract_content
from services.summariser import summarise_content
from services.embedder import generate_embedding #just test

print("Step 1 - Extracting content...")
url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
extracted = extract_content(url)
print(f"Extracted {len(extracted.get('content', ''))} characters")

print("\nStep 2 - Summarising with Gemini...")
result = summarise_content(
    title=extracted['title'],
    content=extracted['content'],
    source_type=extracted['source_type']
)

# print("\nSummary:")
# for i, bullet in enumerate(result['summary'], 1):
#     print(f"  {i}. {bullet}")

# print("\nTags:", result['tags'])

print("Summary:", result['summary'][0])
print("Tags:", result['tags'])

print("\nStep 3 - Generating embedding...")
text_to_embed = " ".join(result['summary']) + " " + " ".join(result['tags'])
embedding = generate_embedding(text_to_embed)
print(f"Embedding generated — vector size: {len(embedding)}")
print("First 5 values:", embedding[:5])