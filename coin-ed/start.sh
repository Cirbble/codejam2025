#!/bin/bash

echo "🚀 Starting Coin'ed Dashboard..."
echo ""
echo "=================================="
echo "  Coin'ed - AI Crypto Sentiment"
echo "=================================="
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

echo "🔧 Starting development server..."
echo ""
echo "📍 Dashboard will be available at:"
echo "   http://localhost:4200"
echo ""
echo "💡 Quick Tips:"
echo "   - Click 'Load Example Scraped Data' to see demo"
echo "   - Toggle switches control agents (currently log to console)"
echo "   - Check QUICKSTART.md for more info"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm start

