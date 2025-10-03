from pathlib import Path
import os
from dotenv import load_dotenv

print("="*80)
print("DEBUGGING ENVIRONMENT LOADING")
print("="*80)

# Check current directory
print(f"\nCurrent directory: {os.getcwd()}")
print(f"Script location: {Path(__file__).parent}")

# Check for .env files
project_root = Path(__file__).parent
print(f"\nSearching for .env files in: {project_root}")

env_files = list(project_root.rglob('.env'))
print(f"\nFound {len(env_files)} .env file(s):")
for env_file in env_files:
    print(f"  - {env_file}")
    print(f"    Size: {env_file.stat().st_size} bytes")
    with open(env_file, 'r') as f:
        content = f.read()
        if 'SERP_API_KEY' in content:
            # Find the key
            for line in content.split('\n'):
                if 'SERP_API_KEY' in line:
                    key = line.split('=')[1].strip()
                    print(f"    SERP_API_KEY: {key[:20]}...")

# Test loading from nodes/.env
print("\n" + "="*80)
print("TESTING: load_dotenv() with no path")
print("="*80)
load_dotenv()
key1 = os.getenv('SERP_API_KEY')
print(f"Result: {key1[:20] if key1 else 'NOT FOUND'}...")

# Clear and test with explicit path
os.environ.pop('SERP_API_KEY', None)

print("\n" + "="*80)
print("TESTING: load_dotenv(dotenv_path='nodes/.env')")
print("="*80)
env_path = Path(__file__).parent / 'nodes' / '.env'
print(f"Loading from: {env_path}")
print(f"File exists: {env_path.exists()}")
load_dotenv(dotenv_path=env_path)
key2 = os.getenv('SERP_API_KEY')
print(f"Result: {key2[:20] if key2 else 'NOT FOUND'}...")

# Check app.py loading
print("\n" + "="*80)
print("SIMULATING APP.PY LOADING")
print("="*80)
os.environ.clear()
exec(open('app.py').read().split('def main')[0])  # Load just the top part of app.py
key3 = os.getenv('SERP_API_KEY')
print(f"After app.py loading: {key3[:20] if key3 else 'NOT FOUND'}...")