import requests
from io import BytesIO
from openai import OpenAI

client = OpenAI(
  api_key="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" #personal key
)

def create_file(client, file_path):
    if file_path.startswith("http://") or file_path.startswith("https://"):
        # Download the file content from the URL
        response = requests.get(file_path)
        file_content = BytesIO(response.content)
        file_name = file_path.split("/")[-1]
        file_tuple = (file_name, file_content)
        result = client.files.create(
            file=file_tuple,
            purpose="assistants"
        )
    else:
        # Handle local file path
        with open(file_path, "rb") as file_content:
            result = client.files.create(
                file=file_content,
                purpose="assistants"
            )
    print(result.id)
    return result.id

# Replace with your own file path or URL
file_id = create_file(client, "./dogfishWikipedia.txt")

#creating a vector store (only one allowed right now)
vector_store = client.vector_stores.create(
    name="knowledge_base"
)
print(vector_store.id)

client.vector_stores.files.create(
    vector_store_id=vector_store.id,
    file_id=file_id
)
#print(result)

result = client.vector_stores.files.list(
vector_store_id=vector_store.id
)
print(result)

response = client.responses.create(
    model="gpt-4o-mini",
    input="What is deep research by OpenAI?",
    tools=[{
        "type": "file_search",
        "vector_store_ids": ["<vector_store_id>"]
    }]
)
print(response)
