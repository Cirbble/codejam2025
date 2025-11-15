#!/bin/bash

echo "🚀 Coin'ed - GitHub Push Helper"
echo "================================"
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    echo "✅ Git initialized"
    echo ""
fi

# Check git status
echo "📋 Checking git status..."
git status --short
echo ""

# Ask for GitHub username
read -p "Enter your GitHub username: " github_username

if [ -z "$github_username" ]; then
    echo "❌ GitHub username is required"
    exit 1
fi

# Ask for repository name
read -p "Enter repository name (default: coin-ed): " repo_name
repo_name=${repo_name:-coin-ed}

# Add all files
echo ""
echo "📦 Staging all files..."
git add .

# Show what will be committed
echo ""
echo "📝 Files to be committed:"
git diff --cached --name-only | head -20
echo ""

# Ask for commit message
read -p "Enter commit message (default: 'Initial commit: Complete Coin'ed dashboard'): " commit_msg
commit_msg=${commit_msg:-"Initial commit: Complete Coin'ed dashboard"}

# Commit
echo ""
echo "💾 Committing changes..."
git commit -m "$commit_msg"

# Check if remote exists
if git remote | grep -q origin; then
    echo ""
    echo "⚠️  Remote 'origin' already exists"
    read -p "Do you want to update it? (y/n): " update_remote
    if [ "$update_remote" = "y" ]; then
        git remote remove origin
        git remote add origin "https://github.com/$github_username/$repo_name.git"
        echo "✅ Remote updated"
    fi
else
    echo ""
    echo "🔗 Adding remote repository..."
    git remote add origin "https://github.com/$github_username/$repo_name.git"
    echo "✅ Remote added: https://github.com/$github_username/$repo_name.git"
fi

# Set main branch
echo ""
echo "🌿 Setting main branch..."
git branch -M main

# Push to GitHub
echo ""
echo "📤 Pushing to GitHub..."
echo "⚠️  Make sure you've created the repository on GitHub first!"
echo "   Visit: https://github.com/new"
echo ""
read -p "Have you created the repository on GitHub? (y/n): " repo_created

if [ "$repo_created" != "y" ]; then
    echo ""
    echo "⏸️  Please create the repository first:"
    echo "   1. Go to https://github.com/new"
    echo "   2. Repository name: $repo_name"
    echo "   3. Make it PUBLIC"
    echo "   4. Don't initialize with README"
    echo "   5. Click 'Create repository'"
    echo ""
    echo "Then run this script again!"
    exit 0
fi

echo ""
echo "🚀 Pushing to GitHub..."
if git push -u origin main; then
    echo ""
    echo "✅ SUCCESS! Your code is now on GitHub!"
    echo ""
    echo "🌐 Repository URL:"
    echo "   https://github.com/$github_username/$repo_name"
    echo ""
    echo "📖 Share this with your team:"
    echo "   git clone https://github.com/$github_username/$repo_name.git"
    echo "   cd $repo_name"
    echo "   npm install"
    echo "   npm start"
    echo ""
    echo "🎉 Happy coding!"
else
    echo ""
    echo "❌ Push failed. Common solutions:"
    echo ""
    echo "1. Make sure you created the repository on GitHub"
    echo "2. Check your GitHub credentials"
    echo "3. Try pushing manually:"
    echo "   git push -u origin main"
    echo ""
    echo "Need help? Check GITHUB_PUSH_GUIDE.md"
fi

