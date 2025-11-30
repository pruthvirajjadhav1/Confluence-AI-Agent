# AI Knowledge Agent for Confluence

An intelligent AI agent that connects to Confluence and helps users find information, answer questions, and get actionable insights from internal documentation.

## Features

- 🔍 **Search Confluence**: Search across all Confluence spaces and pages
- 📚 **Answer with Citations**: Get answers to questions with proper source citations
- 📄 **Document Summarization**: Automatically summarize long documents
- 💡 **Action Suggestions**: Get actionable next steps based on document content
- ⏳ **Loading Indicators**: Visual feedback while the bot processes your queries

## Prerequisites

- Python 3.8+
- Confluence account with API access
- OpenAI API key
- Confluence API token

## Setup

1. **Navigate to the confluence-bot directory**:
   ```bash
   cd confluence-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   
   Create a `.env` file in the confluence-bot directory:
   ```bash
   touch .env
   ```
   
   Edit `.env` and add your credentials:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net
   CONFLUENCE_USERNAME=your_email@company.com
   CONFLUENCE_API_TOKEN=your_confluence_api_token_here
   ```

4. **Get your Confluence API Token**:
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Copy the token and add it to your `.env` file

## Usage

Run the main application:
```bash
python app.py
```

Or run the agent directly:
```bash
python confluence_agent.py
```

## Example Queries

- "What is our company's vacation policy?"
- "Search for documentation about API authentication"
- "Summarize the onboarding process"
- "What are the steps to deploy to production?"
- "Find information about our security protocols"
- "Give me data of Qelstra Technologies – Quarterly Platform Update summary"

## Architecture

- `confluence_connector.py`: Handles all Confluence API interactions
- `confluence_agent.py`: Main agent with tools for search, summarization, citations, and suggestions
- `app.py`: User-friendly CLI interface with loading indicators

## Tools Available

1. **search_confluence**: Search for content in Confluence
2. **search_by_title**: Search by exact or partial title
3. **get_document**: Retrieve full document by ID
4. **summarize_document**: Summarize long documents
5. **answer_with_citations**: Answer questions with proper citations
6. **suggest_actions**: Suggest actionable next steps

## Notes

- The bot uses GPT-4o-mini by default for cost efficiency
- All answers include citations to source documents
- Long documents are automatically summarized when needed
- The agent intelligently chooses which tools to use based on the query
- Loading spinner shows progress while the bot processes queries

## Troubleshooting

**Connection Issues**:
- Verify your Confluence base URL is correct (should end with `.atlassian.net` or your custom domain)
- Ensure your API token is valid and not expired
- Check that your username/email is correct

**No Results Found**:
- Try different search terms
- Verify you have access to the Confluence spaces you're searching
- Check if the content exists in Confluence
- Try using keywords instead of full titles

## License

MIT

