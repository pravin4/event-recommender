import os
import subprocess
from dotenv import load_dotenv

def setup_git():
    # Load environment variables
    load_dotenv()
    
    # Get GitHub token
    github_token = os.getenv('GITHUB_TOKEN')
    
    if not github_token:
        print("Error: GITHUB_TOKEN not found in .env file")
        print("Please create a Personal Access Token on GitHub and add it to your .env file")
        return
    
    # Configure Git to use the token
    try:
        # Set up Git configuration
        subprocess.run(['git', 'config', '--global', 'credential.helper', 'store'])
        
        # Set up the remote URL with the token
        remote_url = f"https://{github_token}@github.com/yourusername/yourrepository.git"
        subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url])
        
        print("Git configuration completed successfully!")
        print("You can now push to GitHub using your token")
        
    except subprocess.CalledProcessError as e:
        print(f"Error setting up Git: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    setup_git() 