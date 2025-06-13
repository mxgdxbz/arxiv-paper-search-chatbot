# SAP Document Analysis Workflow

This guide explains the proper workflow for analyzing Statistical Analysis Plan (SAP) documents.

## 🔄 **Three-Step Process**

### Step 1: Index Documents (Run Once)
```
Use: index_sap_documents()
Purpose: Parse all SAP documents and build a lightweight search index
When: Run this once when you add new documents to the SAP folder
Output: Creates studies_index.json with study_id, phase, therapeutic, indication
```

### Step 2: Find Studies (Search by Criteria)
```
Use: find_studies(phase="Phase III", therapeutic="Oncology", indication="Breast Cancer")
Purpose: Search for study IDs matching your criteria
When: When you need to discover relevant studies
Output: List of matching study IDs with basic information
```

### Step 3: Get Full Study Details (By Study ID)
```
Use: search_primary_analysis(study_id="phase_iii_oncology_study1")
Purpose: Extract complete study information for a specific study
When: After finding relevant study IDs, get full details
Output: Complete study information including endpoints, methods, etc.
```

## 📁 **Directory Structure**
```
sap/
├── _index/
│   └── studies_index.json    # Lightweight index (phase, therapeutic, indication only)
├── phase_i_studies/
│   ├── study1.pdf
│   └── study2.docx
└── phase_ii_studies/
    └── study3.pdf
```

## 🎯 **Individual Document Analysis**
For detailed analysis of a specific document:
```
Use: parse_for_index(file_path)
Purpose: Extract comprehensive information from a single document
When: When you need detailed analysis of a specific SAP document
```

## 📋 **Best Practices**

1. **Initial Setup**: Run `index_sap_documents()` first
2. **Discovery**: Use `find_studies()` to discover relevant studies
3. **Detailed Analysis**: Use `search_primary_analysis(study_id)` for complete information
4. **Regular Updates**: Re-run indexing when adding new documents
5. **Document Parsing Guidance**: Use `document_parsing_guide()` for parsing instructions

## 🔍 **Search Tips**
- Use `find_studies()` with specific terms: "Phase III", "Oncology", "Breast Cancer"
- Leave parameters empty to see all studies: `find_studies()`
- The system matches partial terms and synonyms
- Results include confidence scores and multiple matches

## 💡 **Example Workflow**
```
1. index_sap_documents()                    # Build index
2. find_studies(phase="Phase III")          # Find Phase III studies  
3. search_primary_analysis("study_id_123")  # Get full details
```

This workflow separates indexing, discovery, and detailed analysis for optimal performance.

---

## 🛠️ Tool Summary Table

| Tool/Prompt                  | Main Function                                      | Inputs/Args                        | Output/Relation                        |
|------------------------------|---------------------------------------------------|------------------------------------|----------------------------------------|
| search_papers                | Search arXiv and store paper info                 | topic, max_results                 | papers_info.json, paper IDs            |
| extract_info                 | Get info for a specific paper                     | paper_id                           | Paper metadata                         |
| get_available_folders        | List all paper topic folders                      | -                                  | Folder list                            |
| get_topic_papers             | Get all papers for a topic                        | topic                              | Paper details                          |
| index_sap_documents          | Index all SAP docs                                | -                                  | studies_index.json                     |
| find_studies                 | Search SAP index                                  | phase, therapeutic, indication      | Matching study IDs                     |
| search_primary_analysis      | Full study info for a study_id                    | study_id                           | Comprehensive study info               |
| parse_for_index              | Parse a single document (basic, for indexing)     | file_path                          | Structured info                        |
| generate_search_prompt       | Prompt for LLM paper search                       | topic, num_papers                  | Prompt text                            |
| document_parsing_guide       | Prompt for LLM SAP parsing                        | document_type                      | Prompt text                            |
| sap_workflow_guide           | Prompt for SAP workflow                           | -                                  | Prompt text                            |

---

- **index_sap_documents** calls **parse_for_index** for each document.
- **find_studies** and **search_primary_analysis** both depend on the index built by **index_sap_documents**.
- **search_primary_analysis** uses enhanced extraction helpers for detailed study info.
- **parse_for_index** is also available for direct document analysis.
- **Prompts** guide users/LLMs in using the tools and interpreting results. 