# SingleStore Swarm Agent

A simple Multi-agent RAG System (MARS) that combines SingleStore's vector database capabilities with OpenAI's language models to provide intelligent movie recommendations. The system uses NeMo Guardrails for query classification and input and output validation,and SingleStore agent for querying the database with a structured SQL query. You can extend it to also do exact keyword search and semantic search as part of the same agent.

## Architecture

The application consists of several key components:

1. **SingleStore Database**: Stores movie data and handles vector-based similarity searches and exact keyword search
2. **OpenAI Integration**: Provides natural language understanding and generation
3. **NeMo Guardrails**: Manages conversation flows and ensures appropriate responses
4. **Swarm Agent System**: Coordinates between different components to handle user queries

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-repo/singlestore-swarm-agent.git
```

2. Install the dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in a `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key
SINGLESTORE_HOST=your_singlestore_host
SINGLESTORE_USER=your_singlestore_username
SINGLESTORE_PASSWORD=your_singlestore_password
SINGLESTORE_DATABASE=your_singlestore_database
```

## How It Works

The application follows this flow:

1. **Query Processing**:
   - User input is first processed through NeMo Guardrails
   - Guardrails classify the query into different types (movie recommendations, general questions, etc.)

2. **Query Routing**:
   - Movie-related queries are directed to the SingleStore database
   - General queries are handled directly by the OpenAI LLM
   - Off-topic queries (politics, stock market) are filtered with appropriate responses

3. **Movie Recommendations**:
   - For movie queries, the system searches the SingleStore database
   - Results are ranked by relevance
   - Top 10 recommendations are returned with relevance scores

## Usage

Run the script:
```bash
python singlestore-swarm.py
```

The system will start an interactive session where you can:
- Ask for movie recommendations
- Ask general questions
- Type 'exit' to quit

## Extending the Application

You can expand this application in several ways:

1. **Database Enhancement**:
   - Add more movie metadata (genres, actors, directors)
   - Implement more sophisticated vector similarity searches
   - Add user ratings and viewing history

2. **Query Processing**:
   - Extend NeMo Guardrails rules in `nemo-configs/rails.co`
   - Add new conversation flows
   - Implement more sophisticated query understanding

3. **Response Generation**:
   - Add personalization based on user preferences
   - Implement more detailed movie descriptions
   - Add multi-turn conversations about movies

4. **New Features**:
   - Add collaborative filtering
   - Implement user profiles
   - Add movie clustering
   - Integrate with external movie APIs

To extend the application:

1. **Adding New Guardrails**:
   - Edit `nemo-configs/rails.co` to add new patterns and flows
   - Update `config.yml` if needed for model configurations

2. **Database Modifications**:
   - Add new columns to the movies table in SingleStore
   - Update the search_movies() function in `singlestore-swarm.py`

3. **Agent Enhancement**:
   - Add new functions to the MovieRecommendationAgent
   - Implement new swarm patterns for complex queries

4. **API Integration**:
   - Add new API clients in the main script
   - Implement new data sources for enriched recommendations
