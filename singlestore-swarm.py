from swarm import Swarm, Agent
import singlestoredb as s2
import os
from nemoguardrails import LLMRails, RailsConfig
import openai
from typing import Dict, Any

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize NeMo Guardrails
config = RailsConfig.from_path("nemo-configs/")
rails = LLMRails(config)

def connect_to_singlestore():
    try:
        # Get connection parameters from environment
        host = os.getenv("SINGLESTORE_HOST")
        user = os.getenv("SINGLESTORE_USER")
        password = os.getenv("SINGLESTORE_PASSWORD")
        database = os.getenv("SINGLESTORE_DATABASE")

        # Connect using the working format
        singlestore_connection = s2.connect(host=host,
                                            port=3306,
                                            user=user,
                                            password=password,
                                            database=database)
        return singlestore_connection
    except Exception as e:
        print(f"Error connecting to SingleStore: {e}")
        return None

def get_movie_recommendations(query: str) -> Dict[str, Any]:
    """Fetch movie recommendations from SingleStore"""
    try:
        connection = connect_to_singlestore()
        if not connection:
            return {"error": "Failed to connect to database"}

        sql_query = '''
           SELECT DISTINCT(title), movieId, MATCH(title) AGAINST (?) as relevance
                    FROM movies
                    WHERE MATCH(title) AGAINST (?)
                    ORDER BY relevance DESC
                    LIMIT 10
        '''

        with connection.cursor() as cursor:
            cursor.execute(sql_query, (query, query))
            recommendations = cursor.fetchall()

        # Format recommendations
        formatted_recommendations = {
            "recommendations": [
                {
                    'title': row[0],
                    'match_score': float(row[1]),
                    'avg_rating': float(row[2])
                } for row in recommendations
            ]
        }
        return formatted_recommendations
    except Exception as e:
        return {"error": str(e)}
    finally:
        if connection:
            connection.close()

def direct_llm_response(query: str) -> str:
    """Get response directly from LLM for non-SingleStore queries"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error getting LLM response: {e}"

def is_singlestore_query(response) -> bool:
    """Check if the guardrails response indicates need for SingleStore"""
    # Check if response contains specific indicators from our rails.co rules
    response_text = response.last_message.content.lower()
    return "inform using singlestore" in response_text or \
           "delegate to agent" in response_text

def main():
    # Initialize Swarm client
    client = Swarm()
    
    # Initialize agent with the modified function
    agent = Agent(
        name="MovieRecommendationAgent",
        instructions="You are a helpful movie recommendation agent.",
        functions=[get_movie_recommendations]
    )

    print("Welcome! You can ask me anything. Type 'exit' to quit.")
    
    while True:
        # Get user input
        user_query = input("\nYou: ").strip()
        
        if user_query.lower() == 'exit':
            print("Goodbye!")
            break
        
        try:
            # First pass through guardrails
            guardrails_response = rails.generate(messages=[{"role": "user", "content": user_query}])
            
            # Check if query is blocked by guardrails
            if hasattr(guardrails_response, 'blocked') and guardrails_response.blocked:
                print("I apologize, but I cannot respond to that type of query.")
                continue
            
            # Determine if query needs SingleStore
            if is_singlestore_query(guardrails_response):
                # Use SingleStore agent for movie recommendations
                messages = [{"role": "user", "content": user_query}]
                response = client.run(agent=agent, messages=messages)
                print("Bot:", response.messages[-1]["content"])
            else:
                # Use direct LLM response for general queries
                response = direct_llm_response(user_query)
                print("Bot:", response)
                
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
