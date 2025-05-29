# List of prompt types
promptsList = ["None", "Assistant", "Researcher", "Analyst", "Strategist", "General Schedule GS", "Air Force"]

# Common instructions used across specific prompts
common_instructions = """
You are a J1 Chatbot, designed to answer questions specifically about the uploaded documentation.
When you receive a query, follow these steps:

1. **Response Guidelines**:
   - All answers should be as detailed as possible.
   - Never make up an answer.
   - If there is a section referenced, detail what you found. 
   - If no relevant information is found, respond:
     "I cannot find an adequate answer to your question."


2. **Dataset Status**:
   - If "None" dataset is selected, proceed with answering the query, but with the following caveat:
     "I do not have access to the internet, and all my knowledge is based on information available up to 2022."
"""

# Function to generate a prompt for each role
def generate_prompt(role: str) -> str:
    # Roles that should get the common instructions
    roles_with_common_instructions = ["Assistant", "General Schedule GS", "Air Force"]
    
    if role == "None":
        # For None, return empty string - no specific instructions
        return ""
    elif role in roles_with_common_instructions:
        # For specific roles, combine role name and common instructions
        return f"You are a {role.lower()}. {common_instructions}"
    elif role in ["Researcher", "Analyst", "Strategist"]:
         # For these roles, only provide the role description, NO common instructions
        return f"You are a {role.lower()}."
    else:
        # Fallback for any potentially unknown roles (shouldn't happen with current list)
        return "" 

# Dictionary comprehension to generate the prompts for each role
promptDict = {role: generate_prompt(role) for role in promptsList}
