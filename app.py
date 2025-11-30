"""
AI Knowledge Bot for Confluence - Main Application
Run this file to start the Confluence knowledge bot
"""
import sys
import threading
import time
from confluence_agent import ask, test_connection

# Loading spinner class
class LoadingSpinner:
    """Simple loading spinner for terminal"""
    def __init__(self, message="Thinking"):
        self.message = message
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spinner_index = 0
        self.running = False
        self.thread = None
    
    def _spin(self):
        """Internal spinner animation"""
        while self.running:
            char = self.spinner_chars[self.spinner_index]
            sys.stdout.write(f'\r🤖 Bot: {char} {self.message}...')
            sys.stdout.flush()
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
            time.sleep(0.1)
    
    def start(self):
        """Start the spinner"""
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the spinner"""
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write('\r' + ' ' * 60 + '\r')  # Clear the spinner line
        sys.stdout.flush()

def main():
    print("🤖 AI Knowledge Bot for Internal Docs")
    print("=" * 50)
    
    # Test connection
    print("\nTesting Confluence connection...")
    if test_connection():
        print("✅ Connected to Confluence successfully!")
    else:
        print("❌ Failed to connect to Confluence.")
        print("Please check your .env file and ensure you have:")
        print("  - CONFLUENCE_BASE_URL")
        print("  - CONFLUENCE_USERNAME")
        print("  - CONFLUENCE_API_TOKEN")
        print("  - OPENAI_API_KEY")
        return
    
    print("\n" + "=" * 50)
    print("Bot is ready! I can help you:")
    print("  • Search Confluence documents")
    print("  • Answer questions with citations")
    print("  • Summarize long documents")
    print("  • Suggest actionable next steps")
    print("\nType 'exit' to quit.\n")
    
    while True:
        try:
            query = input("You: ").strip()
            if query.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye! 👋")
                break
            
            if not query:
                continue
            
            # Show loading spinner
            spinner = LoadingSpinner("Thinking")
            spinner.start()
            
            try:
                response = ask(query)
                spinner.stop()
                print("🤖 Bot:", response)
                print()
            except Exception as e:
                spinner.stop()
                print(f"\n⚠️ Error: {e}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n⚠️ Error: {e}\n")

if __name__ == "__main__":
    main()

