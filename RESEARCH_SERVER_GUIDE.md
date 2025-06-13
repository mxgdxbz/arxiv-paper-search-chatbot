# 🔬 Research Server & MCP Chatbot Guide

## 🚀 Quick Start

### 1. Run the MCP Chatbot
```bash
uv run mcp_chatbot.py
```

### 2. Basic Commands in Chatbot
```
/prompts                    # List all available prompts
/prompt <name> <args>       # Execute a specific prompt
@folders                    # See available paper topics
@<topic>                    # Access papers in a topic
quit                        # Exit the chatbot
```

## 🧪 Testing Your Setup

### Option 1: Run Comprehensive Tests
```bash
uv run test_research_server.py
```

### Option 2: Manual Testing in Chatbot
```
# Start chatbot
uv run mcp_chatbot.py

# Then try these commands:
/prompts
/prompt sap_workflow_guide
parse_document_content sap/test_study.txt
index_sap_documents
search_primary_analysis Phase III Oncology Melanoma
```

## 🔧 Available Tools

### 📄 Document Parsing
- **`parse_document_content`** - Parse individual documents (PDF, DOCX, TXT)
- **`index_sap_documents`** - Index all SAP documents for fast searching
- **`search_primary_analysis`** - Search indexed studies by phase/therapeutic/indication

### 📚 Academic Papers
- **`search_papers`** - Search arXiv for academic papers
- **`extract_info`** - Get information about specific papers

### 📋 Prompts & Guides
- **`sap_workflow_guide`** - Complete workflow guide for SAP analysis
- **`document_parsing_guide`** - Instructions for document parsing
- **`generate_search_prompt`** - Generate prompts for paper searches

## 🎯 Common Use Cases

### Case 1: Analyze a New SAP Document
```
1. Add document to sap/ folder
2. Run: parse_document_content <file_path>
3. Review extracted information
```

### Case 2: Search for Similar Studies
```
1. Run: index_sap_documents (if not done before)
2. Run: search_primary_analysis <phase> <therapeutic> <indication>
3. Review matching studies
```

### Case 3: Research Academic Literature
```
1. Run: search_papers <topic> <max_results>
2. Run: extract_info <paper_id>
3. Use @folders and @<topic> for organized access
```

## 📁 Directory Structure
```
MCP/
├── sap/                           # SAP documents
│   ├── _index/                    # Auto-generated search index
│   │   └── studies_index.json
│   ├── test_study.txt            # Test document
│   └── *.pdf, *.docx             # Your SAP documents
├── papers/                        # Academic papers (auto-created)
│   └── <topic>/
│       └── papers_info.json
├── research_server.py             # Main MCP server
├── mcp_chatbot.py                # Interactive chatbot
├── test_research_server.py       # Comprehensive test suite
└── server_config.json            # MCP server configuration
```

## 🔍 Example Interactions

### Parsing a Document
```
Query: parse_document_content sap/test_study.txt

Result: 
{
  "title": "A Phase III Randomized, Double-Blind, Placebo-Controlled Study...",
  "detected_phase": "Phase III",
  "detected_therapeutic": "Oncology", 
  "detected_indication": "Breast Cancer",
  "sample_size": "450",
  "extraction_confidence": "High"
}
```

### Searching Studies
```
Query: search_primary_analysis Phase III Oncology Melanoma

Result: Matching study with detailed information including:
- Study design and endpoints
- Sample size and statistical methods
- Treatment details and visit schedule
```

### Getting Workflow Guidance
```
Query: /prompt sap_workflow_guide

Result: Complete step-by-step guide for SAP document analysis
```

## ⚡ Performance Tips

1. **Index First**: Run `index_sap_documents` before searching
2. **Batch Processing**: Index multiple documents at once
3. **Specific Searches**: Use precise terms for better matching
4. **Resource Management**: Use `@folders` to see available topics

## 🐛 Troubleshooting

### Common Issues
- **"No search index found"**: Run `index_sap_documents` first
- **"File not found"**: Check file paths are relative to MCP directory
- **"Error parsing PDF"**: Ensure PyPDF2 is installed (`uv sync`)

### Debug Commands
```bash
# Check dependencies
uv sync

# Test server connection
uv run mcp_chatbot.py

# Run comprehensive tests
uv run test_research_server.py
```

## 🎉 Success Indicators

✅ **Working Correctly When You See:**
- Chatbot connects to research server
- Tools and prompts are listed
- Documents parse successfully
- Search returns relevant results
- Academic papers are found and stored

Your research server is now ready for clinical document analysis! 🚀 