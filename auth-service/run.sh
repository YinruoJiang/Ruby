#!/bin/bash

# Print with colors
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up auth service...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install requirements
echo -e "${GREEN}Installing requirements...${NC}"
pip install -r requirements.txt

# Run the service
echo -e "${GREEN}Starting auth service...${NC}"
echo -e "${GREEN}Service will be available at http://localhost:3002${NC}"
echo -e "${GREEN}Press Ctrl+C to stop the service${NC}"
python app.py 