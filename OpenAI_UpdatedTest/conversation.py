import os
import openai
from rich.console import Console
from rich.markdown import Markdown

# Initialize the OpenAI client
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    openai_api_key = input("Please enter your OpenAI API key: ")
    os.environ["OPENAI_API_KEY"] = openai_api_key

client = openai.OpenAI(api_key=openai_api_key)
console = Console()

# Vector store ID (from the provided documentation)
VECTOR_STORE_ID = "vs_68070872a1208191a8d3f5591d19db91"

def print_markdown(text):
    """Print text as markdown."""
    console.print(Markdown(text))

def chat_with_file_search():
    """Main chat loop with file search capabilities."""
    console.print("[bold green]File Search Enabled Chat[/bold green]")
    console.print("[italic]Type 'exit' to quit the chat[/italic]")
    console.print()
    
    previous_response_id = None
    
    while True:
        # Get user input
        user_input = input("\n[You]: ")
        
        if user_input.lower() == 'exit':
            console.print("[bold green]Thank you for chatting![/bold green]")
            break
        
        try:
            # Create a response with file search tool
            response = client.responses.create(
                model="gpt-4o-mini",
                input=user_input,
                previous_response_id=previous_response_id,
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": [VECTOR_STORE_ID]
                }],
                include=["file_search_call.results"]
            )
            
            # Save the response ID for conversation continuity
            previous_response_id = response.id
            
            # Print the assistant's response
            console.print("\n[Assistant]:", style="bold blue")
            print_markdown(response.output_text)
            
            # If file search was used, print the citations
            if hasattr(response, 'file_search_calls') and response.file_search_calls:
                console.print("\n[Citations]:", style="bold yellow")
                for file_search_call in response.file_search_calls:
                    if hasattr(file_search_call, 'search_results') and file_search_call.search_results:
                        for i, result in enumerate(file_search_call.search_results, 1):
                            console.print(f"[{i}] File: {result.file.filename}")
                            console.print(f"    Excerpt: {result.text[:100]}...")
        
        except Exception as e:
            console.print(f"\n[bold red]Error: {str(e)}[/bold red]")

if __name__ == "__main__":
    # Check if the API key is valid
    try:
        client.models.list()
        chat_with_file_search()
    except Exception as e:
        console.print(f"[bold red]Failed to initialize: {str(e)}[/bold red]")
        console.print("[bold yellow]Make sure your API key is correct and has access to the file search feature.[/bold yellow]")