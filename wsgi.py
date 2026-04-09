import sys
import os

# Garante que o Python encontre a pasta 'api'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'api')))

from api.app import app

if __name__ == "__main__":
    app.run()