#!/bin/bash

# AI Prompt Engineer - Setup Script
echo "🚀 Setting up AI Prompt Engineer..."

# Check for required tools
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }

echo "✅ Prerequisites check passed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API keys and credentials"
else
    echo "✅ .env file already exists"
fi

# Backend setup
echo ""
echo "🔧 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Backend setup complete"
cd ..

# Frontend setup
echo ""
echo "🎨 Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
else
    echo "✅ npm dependencies already installed"
fi

echo "✅ Frontend setup complete"
cd ..

echo ""
echo "✨ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env file with your credentials:"
echo "   - Auth0 configuration"
echo "   - OpenAI API key"
echo "   - Pinecone API key"
echo "   - AWS S3 credentials"
echo "   - LangSmith API key (optional)"
echo ""
echo "2. Start services:"
echo "   Option A - Docker (recommended):"
echo "     docker-compose up -d"
echo ""
echo "   Option B - Manual:"
echo "     Terminal 1 - Backend:"
echo "       cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "     Terminal 2 - Frontend:"
echo "       cd frontend && npm run dev"
echo ""
echo "3. Access the application:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📚 For more information, see README.md"
