from swarm import Swarm, Agent
import singlestoredb as s2
import os
from nemoguardrails import LLMRails, RailsConfig
from openai import OpenAI
from typing import Dict, Any, List, Callable, Tuple
import numpy as np

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize NeMo Guardrails
config = RailsConfig.from_path("nemo-configs/")
rails = LLMRails(config)

# Global connection and query
singlestore_conn = None
current_query = ""

def connect_to_singlestore():
    """Establish connection to SingleStore"""
    try:
        # Get connection parameters from environment
        host = os.getenv("SINGLESTORE_HOST")
        user = os.getenv("SINGLESTORE_USER")
        password = os.getenv("SINGLESTORE_PASSWORD")
        database = os.getenv("SINGLESTORE_DATABASE")

        # Connect using the working format
        return s2.connect(host=host,
                         port=3306,
                         user=user,
                         password=password,
                         database=database)
    except Exception as e:
        print(f"Error connecting to SingleStore: {e}")
        return None

def search_movies() -> str:
    """Core function to search movies in SingleStore"""
    global singlestore_conn, current_query
    
    try:
        if not singlestore_conn:
            singlestore_conn = connect_to_singlestore()
        if not singlestore_conn:
            return "Failed to connect to database"

        sql_query = '''
           SELECT title, MATCH(title) AGAINST (?) as relevance
           FROM movies
           WHERE MATCH(title) AGAINST (?)
           ORDER BY relevance DESC
           LIMIT 10
        '''

        cursor = singlestore_conn.cursor()
        cursor.execute(sql_query, (current_query, current_query))
        
        # Convert cursor results to numpy array for easier handling
        results = np.array(cursor.fetchall())
        cursor.close()

        if len(results) == 0:
            return "No movie recommendations found for your query."
            
        response = "Here are some movie recommendations:\n"
        for title, relevance in results:
            response += f"- {title} (Relevance: {float(relevance):.2f})\n"
            
        return response
            
    except Exception as e:
        if singlestore_conn:
            singlestore_conn.close()
            singlestore_conn = None
        return f"Error getting recommendations: {e}"

def direct_llm_response(query: str) -> str:
    """Get response directly from LLM for non-SingleStore queries"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content or "No response generated"
    except Exception as e:
        return f"Error getting LLM response: {e}"

def is_singlestore_query(response) -> bool:
    """Check if the guardrails response indicates need for SingleStore"""
    try:
        # Check if response contains specific indicators from our rails.co rules
        response_text = response.last_message.content.lower()
        return "inform using singlestore" in response_text or \
               "delegate to agent" in response_text
    except AttributeError:
        # If we can't access the response content as expected,
        # default to treating it as a non-SingleStore query
        return False

def main():
    global current_query
    
    # Initialize Swarm client
    swarm_client = Swarm()
    
    # Initialize agent with the movie recommendation function
    agent = Agent(
        name="MovieRecommendationAgent",
        instructions="You are a helpful movie recommendation agent.",
        functions=[search_movies]
    )

    print("Welcome! You can ask me anything. Type 'exit' to quit.")
    
    while True:
        # Get user input
        user_query = input("\nYou: ").strip()
        
        if user_query.lower() == 'exit':
            print("Goodbye!")
            if singlestore_conn:
                singlestore_conn.close()
            break
        
        try:
            # First pass through guardrails
            guardrails_response = rails.generate(messages=[{"role": "user", "content": user_query}])
            
            # Check if query needs SingleStore
            if is_singlestore_query(guardrails_response):
                # Update current query for the search function
                current_query = user_query
                
                # Use SingleStore agent for movie recommendations
                messages = [{"role": "user", "content": user_query}]
                response = swarm_client.run(agent=agent, messages=messages)
                print("Bot:", response.messages[-1]["content"])
            else:
                # Use direct LLM response for general queries
                response = direct_llm_response(user_query)
                print("Bot:", response)
                
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
