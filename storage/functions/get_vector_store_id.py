import re

def get_vector_store_id_from_server():
    try:
        server_path = "backend\server.py"
        with open(server_path, 'r') as file:
            content = file.read()
            # Look for the vector store ID in the tools configuration
            match = re.search(r'"vector_store_ids":\s*\["([^"]+)"\]', content)
            if match:
                return match.group(1)
            return None
    except Exception as e:
        print(f"Error reading vector store ID from server.py: {e}")
        return None