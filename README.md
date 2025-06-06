# arXiv Paper Search Chatbot

A Python-based chatbot that searches for academic papers on arXiv and provides information about them using Anthropic's Claude AI.

## Features

- **Paper Search**: Search for papers on arXiv by topic and store their information (title, authors, summary, PDF URL, publication date)
- **Paper Information Retrieval**: Extract detailed information about specific papers using their arXiv IDs
- **Interactive Chat Interface**: Chat with an AI assistant that can search and provide information about academic papers
- **Organized Storage**: Papers are organized by topic in JSON files for easy access

## Setup

### Prerequisites

- Python 3.7+
- Anthropic API key

### Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd MCP
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install arxiv python-dotenv anthropic ipykernel
   ```

4. Set up your environment variables:
   - Create a `.env` file in the project root
   - Add your Anthropic API key:
     ```
     ANTHROPIC_API_KEY=your_api_key_here
     ```
   - Get your API key from: https://console.anthropic.com/

5. (Optional) If using Jupyter Notebook, register the kernel:
   ```bash
   python -m ipykernel install --user --name=venv
   ```

## Usage

Open the `notebook.ipynb` file in Jupyter Notebook and run the cells. The main functions available are:

### Search Papers
```python
search_papers("machine learning", max_results=5)
```

### Extract Paper Information
```python
extract_info("2501.02346v1")
```

### Interactive Chat
```python
chat_loop()
```

## Project Structure

```
MCP/
├── notebook.ipynb          # Main Jupyter notebook with all functionality
├── papers/                 # Directory where paper information is stored
│   └── [topic]/           # Topic-specific subdirectories
│       └── papers_info.json  # JSON files with paper details
├── .env                   # Environment variables (not tracked in git)
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## Tools Available

1. **search_papers**: Searches arXiv for papers on a given topic and stores their metadata
2. **extract_info**: Retrieves stored information about a specific paper by its arXiv ID

## Notes

- The chatbot does not persist memory across queries
- Papers are stored locally in JSON format, organized by topic
- The system uses Claude AI for natural language processing and responses

## License

This project is open source and available under the MIT License. 