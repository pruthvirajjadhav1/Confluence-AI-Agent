"""
AI Knowledge Bot for Confluence
Main agent that orchestrates all tools and capabilities
"""
import os
import re
from typing import List, Dict
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from confluence_connector import ConfluenceConnector

load_dotenv()

# Initialize Confluence connector
def get_confluence_connector() -> ConfluenceConnector:
    """Get initialized Confluence connector from environment variables"""
    base_url = os.getenv("CONFLUENCE_BASE_URL")
    username = os.getenv("CONFLUENCE_USERNAME")
    api_token = os.getenv("CONFLUENCE_API_TOKEN")
    
    if not all([base_url, username, api_token]):
        raise ValueError(
            "Missing Confluence credentials. Please set CONFLUENCE_BASE_URL, "
            "CONFLUENCE_USERNAME, and CONFLUENCE_API_TOKEN in your .env file"
        )
    
    return ConfluenceConnector(base_url, username, api_token)

# Initialize connector (will be created when needed)
confluence = None

def get_confluence():
    """Lazy initialization of Confluence connector"""
    global confluence
    if confluence is None:
        confluence = get_confluence_connector()
    return confluence

# Initialize LLM
llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")

# Tool: Search Confluence
@tool
def search_confluence(query: str) -> str:
    """
    Search for content in Confluence based on a query.
    Uses multiple search strategies to find relevant pages.
    Returns relevant pages with titles, excerpts, and URLs.
    
    Args:
        query: The search query string (can be a title, keywords, or full text)
        
    Returns:
        Formatted string with search results including citations
    """
    try:
        connector = get_confluence()
        # Increase limit to get more results
        results = connector.search_content(query, limit=10)
        
        if not results:
            return (
                f"No results found for query: '{query}'\n\n"
                f"Suggestions:\n"
                f"- Try using keywords instead of the full title\n"
                f"- Check spelling\n"
                f"- Try searching for a specific part of the title\n"
                f"- Ensure you have access to the Confluence space"
            )
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            excerpt = result.get('excerpt', 'No excerpt available')
            if not excerpt or excerpt == 'No excerpt available':
                # Try to get excerpt from body if available
                body = result.get('body', '')
                if body:
                    excerpt = clean_html(body)[:200] + "..."
            
            formatted_results.append(
                f"[{i}] {result['title']}\n"
                f"   Space: {result['space']}\n"
                f"   URL: {result['url']}\n"
                f"   Content ID: {result['id']}\n"
                f"   Excerpt: {excerpt[:200]}...\n"
            )
        
        return f"Found {len(results)} results for '{query}':\n\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"Error searching Confluence: {str(e)}"

# Tool: Get Full Document
@tool
def get_document(content_id: str) -> str:
    """
    Retrieve a full document from Confluence by its content ID.
    Use this when you need the complete content of a specific page.
    
    Args:
        content_id: The Confluence content ID (usually found in URLs or search results)
        
    Returns:
        Full document content with metadata and citation
    """
    try:
        connector = get_confluence()
        doc = connector.get_content_by_id(content_id)
        
        if not doc:
            return f"Document with ID {content_id} not found."
        
        # Clean HTML tags for better readability
        body_text = clean_html(doc.get("body", ""))
        
        return (
            f"Document: {doc['title']}\n"
            f"Space: {doc['space']}\n"
            f"URL: {doc['url']}\n"
            f"Version: {doc.get('version', 'N/A')}\n"
            f"Last Modified: {doc.get('lastModified', 'N/A')}\n\n"
            f"Content:\n{body_text}\n\n"
            f"Citation: {doc['url']}"
        )
    except Exception as e:
        return f"Error retrieving document: {str(e)}"

# Tool: Summarize Document
@tool
def summarize_document(content_id: str, max_length: int = 500) -> str:
    """
    Summarize a long document from Confluence.
    Use this when a document is too long and needs to be condensed.
    
    Args:
        content_id: The Confluence content ID
        max_length: Maximum length of the summary in characters
        
    Returns:
        Concise summary with citation
    """
    try:
        connector = get_confluence()
        doc = connector.get_content_by_id(content_id)
        
        if not doc:
            return f"Document with ID {content_id} not found."
        
        body_text = clean_html(doc.get("body", ""))
        
        # Use LLM to summarize if document is long
        if len(body_text) > max_length:
            summary_prompt = f"""Please provide a concise summary of the following document in {max_length} characters or less:

Title: {doc['title']}
Content: {body_text[:3000]}  # Limit input to avoid token limits

Summary:"""
            
            summary_llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
            summary = summary_llm.invoke(summary_prompt).content
        else:
            summary = body_text[:max_length]
        
        return (
            f"Summary of: {doc['title']}\n"
            f"Space: {doc['space']}\n"
            f"URL: {doc['url']}\n\n"
            f"{summary}\n\n"
            f"Citation: {doc['url']}"
        )
    except Exception as e:
        return f"Error summarizing document: {str(e)}"

# Tool: Search by Title
@tool
def search_by_title(title_query: str) -> str:
    """
    Search for Confluence pages by title. Use this when you know the exact or partial title.
    This is more precise than general search.
    
    Args:
        title_query: The title or part of the title to search for
        
    Returns:
        Formatted string with matching pages
    """
    try:
        connector = get_confluence()
        # Use title-specific search
        results = connector.search_by_title(title_query, limit=10)
        
        if not results:
            return f"No pages found with title matching: '{title_query}'"
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"[{i}] {result['title']}\n"
                f"   Space: {result['space']}\n"
                f"   URL: {result['url']}\n"
                f"   Content ID: {result['id']}\n"
            )
        
        return f"Found {len(results)} pages with title matching '{title_query}':\n\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"Error searching by title: {str(e)}"

# Tool: Answer Query with Citations
@tool
def answer_with_citations(query: str) -> str:
    """
    Answer a query by searching Confluence and providing citations.
    This tool searches for relevant content and formats the answer with proper citations.
    
    Args:
        query: The user's question
        
    Returns:
        Answer with citations to source documents
    """
    try:
        connector = get_confluence()
        # Increase limit to get more context
        results = connector.search_content(query, limit=5)
        
        if not results:
            return f"I couldn't find any relevant information for: '{query}'"
        
        # Extract content from top results
        context = []
        citations = []
        
        for result in results:
            # Get full content for better context
            full_doc = connector.get_content_by_id(result['id'])
            if full_doc:
                body_text = clean_html(full_doc.get("body", ""))[:2000]  # Limit length
                context.append(f"Title: {full_doc['title']}\nContent: {body_text}")
                citations.append({
                    "title": full_doc['title'],
                    "url": full_doc['url']
                })
        
        # Use LLM to generate answer from context
        answer_prompt = f"""Based on the following Confluence documents, answer the user's question.
Provide a clear, accurate answer and cite the sources.

User Question: {query}

Documents:
{chr(10).join([f"Document {i+1}: {ctx}" for i, ctx in enumerate(context)])}

Answer the question using information from these documents. At the end, list all citations in the format:
[1] Title - URL
[2] Title - URL

Answer:"""
        
        answer_llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        answer = answer_llm.invoke(answer_prompt).content
        
        # Ensure citations are included
        if not any(citation['url'] in answer for citation in citations):
            citation_text = "\n\nCitations:\n" + "\n".join(
                [f"[{i+1}] {cit['title']} - {cit['url']}" 
                 for i, cit in enumerate(citations)]
            )
            answer += citation_text
        
        return answer
    except Exception as e:
        return f"Error answering query: {str(e)}"

# Tool: Suggest Actions
@tool
def suggest_actions(query: str, context: str = "") -> str:
    """
    Suggest actionable next steps based on a query or document context.
    Use this to provide users with recommended actions they can take.
    
    Args:
        query: The user's query or question
        context: Optional context from documents
        
    Returns:
        List of suggested actions
    """
    try:
        # Search for relevant content
        connector = get_confluence()
        results = connector.search_content(query, limit=3)
        
        context_text = ""
        if results:
            for result in results:
                doc = connector.get_content_by_id(result['id'])
                if doc:
                    body_text = clean_html(doc.get("body", ""))[:1500]
                    context_text += f"\n\nDocument: {doc['title']}\n{body_text}"
        
        if context:
            context_text = context + context_text
        
        action_prompt = f"""Based on the following query and context, suggest 3-5 actionable next steps for the user.

Query: {query}

Context: {context_text}

Provide suggestions in a numbered list format. Each suggestion should be:
- Specific and actionable
- Relevant to the query
- Based on the context provided

Suggestions:"""
        
        action_llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        suggestions = action_llm.invoke(action_prompt).content
        
        return suggestions
    except Exception as e:
        return f"Error generating suggestions: {str(e)}"

# Helper function to clean HTML
def clean_html(html_text: str) -> str:
    """Remove HTML tags and decode entities"""
    if not html_text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_text)
    
    # Decode common HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

# Create agent with all tools
tools = [
    search_confluence,
    search_by_title,
    get_document,
    summarize_document,
    answer_with_citations,
    suggest_actions
]

system_prompt = """You are an AI Knowledge Bot for Internal Documentation. Your role is to help users find information in Confluence and answer their questions.

Capabilities:
1. Search Confluence for relevant documents (search_confluence)
2. Search by exact or partial title (search_by_title) - use this when user mentions a specific document title
3. Retrieve and display full documents with citations (get_document)
4. Summarize long documents (summarize_document)
5. Answer questions with proper citations (answer_with_citations)
6. Suggest actionable next steps (suggest_actions)

Always:
- Provide citations when referencing documents
- When user asks for a specific document by title, use search_by_title first
- Use search_confluence for general searches
- Use answer_with_citations for comprehensive answers
- Use summarize_document for long documents
- Use suggest_actions to help users with next steps
- Be helpful, accurate, and cite your sources
- If initial search fails, try different search strategies or keywords

When answering:
- Be concise but thorough
- Always include document URLs as citations
- If you don't know something, say so and suggest searching Confluence
- Format citations clearly with [1], [2], etc.
- When user asks for "data" or "summary" of a document, first find it, then retrieve and summarize it
"""

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)

def ask(question: str) -> str:
    """
    Main function to ask the bot a question
    
    Args:
        question: User's question
        
    Returns:
        Bot's response
    """
    try:
        response = agent.invoke({
            "messages": [HumanMessage(content=question)]
        })
        return response["messages"][-1].content
    except Exception as e:
        return f"Error: {str(e)}"

def test_connection() -> bool:
    """Test Confluence connection"""
    try:
        connector = get_confluence()
        return connector.test_connection()
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

