import arxiv
import json
import os
import re
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP

# Document parsing imports
try:
    import PyPDF2
    from docx import Document
except ImportError:
    PyPDF2 = None
    Document = None
    print("Warning: PyPDF2 and/or python-docx not installed. Document parsing will not be available.")

PAPER_DIR = "papers"
SAP_DIR = "sap"

# Initialize FastMCP server
mcp = FastMCP("research")


def parse_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    if not PyPDF2:
        return ""
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {str(e)}")
        return ""

def parse_docx(file_path: str) -> str:
    """Extract text from Word document."""
    if not Document:
        return ""
    
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error parsing DOCX {file_path}: {str(e)}")
        return ""



def parse_document(file_path: str) -> str:
    """Parse document based on file extension."""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        return parse_pdf(file_path)
    elif file_ext in ['.docx', '.doc']:
        return parse_docx(file_path)
    else:
        print(f"Unsupported file format: {file_ext}")
        return ""

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
    
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve (default: 5)
        
    Returns:
        List of paper IDs found in the search
    """
    
    # Use arxiv to find the papers 
    client = arxiv.Client()

    # Search for the most relevant articles matching the queried topic
    search = arxiv.Search(
        query = topic,
        max_results = max_results,
        sort_by = arxiv.SortCriterion.Relevance
    )

    papers = client.results(search)
    
    # Create directory for this topic
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    
    file_path = os.path.join(path, "papers_info.json")

    # Try to load existing papers info
    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    # Process each paper and add to papers_info  
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        paper_info = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }
        papers_info[paper.get_short_id()] = paper_info
    
    # Save updated papers_info to json file
    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)
    
    print(f"Results are saved in: {file_path}")
    
    return paper_ids

@mcp.tool()
def index_sap_documents() -> str:
    """
    Index all SAP documents by parsing them and storing the results.
    This should be run once to build the search index.
    
    Returns:
        Summary of indexing results
    """
    if not os.path.exists(SAP_DIR):
        return f"SAP directory not found at {SAP_DIR}. Please create it and add documents."
    
    indexed_count = 0
    error_count = 0
    
    # Create index directory
    index_dir = os.path.join(SAP_DIR, "_index")
    os.makedirs(index_dir, exist_ok=True)
    
    all_studies = {}
    
    # Walk through all documents
    for root, dirs, files in os.walk(SAP_DIR):
        # Skip the index directory itself
        if "_index" in root:
            continue
            
        for file in files:
            if file.endswith(('.pdf', '.docx', '.doc')):
                file_path = os.path.join(root, file)
                
                try:
                    # Parse the document
                    parsed_result = parse_for_index(file_path)
                    study_data = json.loads(parsed_result)
                    
                    # Create unique study ID
                    study_id = f"{os.path.basename(root)}_{os.path.splitext(file)[0]}"
                    
                    # Store only essential fields in index
                    all_studies[study_id] = {
                        'detected_phase': study_data.get('detected_phase', 'Unknown'),
                        'detected_therapeutic': study_data.get('detected_therapeutic', 'Unknown'),
                        'detected_indication': study_data.get('detected_indication', 'Unknown'),
                        'source_file': file_path
                    }
                    
                    indexed_count += 1
                    
                except Exception as e:
                    print(f"Error indexing {file_path}: {str(e)}")
                    error_count += 1
    
    # Save the complete index
    index_file = os.path.join(index_dir, "studies_index.json")
    with open(index_file, "w") as f:
        json.dump(all_studies, f, indent=2)
    
    return f"Indexing complete: {indexed_count} documents indexed, {error_count} errors. Index saved to {index_file}"

@mcp.tool()
def search_primary_analysis(study_id: str) -> str:
    """
    Get comprehensive study information for a specific study ID with enhanced extraction.
    Provides detailed sample size analysis, statistical methods, and structured study information.
    
    Args:
        study_id: The unique study identifier from the index
        
    Returns:
        JSON string with comprehensive study information including detailed sample size breakdown,
        statistical analysis plan, and study design information
    """
    
    # Check if index exists
    index_file = os.path.join(SAP_DIR, "_index", "studies_index.json")
    if not os.path.exists(index_file):
        return f"No search index found. Please run index_sap_documents first to build the search index."
    
    try:
        # Load the index
        with open(index_file, "r") as f:
            all_studies = json.load(f)
        
        # Find the study
        if study_id not in all_studies:
            available_ids = list(all_studies.keys())
            return f"Study ID '{study_id}' not found. Available study IDs: {available_ids}"
        
        study_info = all_studies[study_id]
        source_file = study_info['source_file']
        
        # Parse the complete document with enhanced extraction
        text_content = parse_document(source_file)
        if not text_content:
            return f"Error: Could not extract text from {source_file}"
        
        # Enhanced comprehensive analysis
        comprehensive_analysis = _enhanced_document_analysis(text_content, source_file, study_id)
        
        return json.dumps(comprehensive_analysis, indent=2)
        
    except Exception as e:
        return f"Error retrieving comprehensive study information: {str(e)}"

def _enhanced_document_analysis(text_content: str, file_path: str, study_id: str) -> dict:
    """
    Enhanced document analysis with comprehensive extraction.
    """
    
    # Basic extraction patterns (enhanced)
    extracted_info = {}
    
    # Enhanced regex patterns for better extraction
    enhanced_patterns = {
        'title': [
            r'(?i)(?:title|study title):\s*(.+?)(?:\n|$)',
            r'(?i)^(.+?)\s*(?:protocol|study)',
            r'(?i)study:\s*(.+?)(?:\n|$)',
            r'(?i)(?:protocol|study)\s+title[:\s]*(.+?)(?:\n|$)'
        ],
        'pharma': [
            r'(?i)(?:sponsor|pharmaceutical company|company|pharma):\s*(.+?)(?:\n|$)',
            r'(?i)(?:sponsored by|developed by):\s*(.+?)(?:\n|$)'
        ],
        'study_design': [
            r'(?i)(?:study design|design|study type):\s*(.+?)(?:\n|$)',
            r'(?i)(randomized.{0,100}controlled.{0,50}study)',
            r'(?i)(double.?blind.{0,50}placebo.?controlled)',
            r'(?i)(multicenter.{0,50}study)',
            r'(?i)(phase\s+[i1v]+.{0,100}study)'
        ],
        'primary_endpoint': [
            r'(?i)(?:primary endpoint|primary outcome|primary objective):\s*(.+?)(?:\n|\.|;)',
            r'(?i)primary.{0,30}endpoint[:\s]*(.+?)(?:\n|\.|;)',
            r'(?i)(?:primary efficacy endpoint):\s*(.+?)(?:\n|\.|;)'
        ],
        'secondary_endpoints': [
            r'(?i)(?:secondary endpoints?|secondary outcomes?):\s*(.+?)(?:\n\n|\. Primary|\. Secondary)',
            r'(?i)secondary.{0,30}endpoint[s]?[:\s]*(.+?)(?:\n\n|\. )'
        ],
        'statistical_method': [
            r'(?i)(?:statistical method|primary analysis|statistical approach|analysis method):\s*(.+?)(?:\n|$)',
            r'(?i)(MMRM|mixed.?model|ANCOVA|t.?test|chi.?square|logistic regression|cox regression|kaplan.?meier).{0,100}',
            r'(?i)(?:analysis.{0,30}performed.{0,30}using):\s*(.+?)(?:\n|$)'
        ],
        'randomization': [
            r'(?i)(?:randomization|randomisation|randomized):\s*(.+?)(?:\n|$)',
            r'(?i)(?:subjects.{0,50}randomized.{0,50}to)(.+?)(?:\n|$)',
            r'(?i)(?:patients.{0,50}randomized.{0,50}in.{0,20}ratio)(.+?)(?:\n|$)'
        ]
    }
    
    # Extract using enhanced patterns
    for field, field_patterns in enhanced_patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text_content, re.DOTALL)
            if match:
                extracted_info[field] = match.group(1).strip() if match.groups() else match.group(0).strip()
                break
    
    # Enhanced sample size analysis
    sample_size_info = _extract_sample_size_details(text_content)
    
    # Extract visit schedule details
    visit_schedule = _extract_visit_schedule(text_content)
    
    # Extract treatment arms
    treatment_arms = _extract_treatment_arms(text_content)
    
    # Extract inclusion/exclusion criteria
    criteria = _extract_inclusion_exclusion_criteria(text_content)
    
    # Extract statistical analysis details
    statistical_details = _extract_statistical_details(text_content)
    
    # Phase detection (using improved logic from parse_document_content)
    detected_phase = _detect_phase(extracted_info.get('title', ''), os.path.basename(file_path), extracted_info.get('study_design', ''))
    
    # Compile comprehensive analysis
    comprehensive_analysis = {
        'study_identification': {
            'study_id': study_id,
            'title': extracted_info.get('title', f"Document: {os.path.basename(file_path)}"),
            'sponsor': extracted_info.get('pharma', 'Not specified'),
            'detected_phase': detected_phase,
            'source_file': file_path
        },
        
        'study_design': {
            'design_type': extracted_info.get('study_design', 'Not specified'),
            'randomization': extracted_info.get('randomization', 'Not specified'),
            'treatment_arms': treatment_arms
        },
        
        'sample_size_analysis': sample_size_info,
        
        'endpoints_and_objectives': {
            'primary_endpoint': extracted_info.get('primary_endpoint', 'Not specified'),
            'secondary_endpoints': extracted_info.get('secondary_endpoints', 'Not specified')
        },
        
        'statistical_analysis_plan': {
            'primary_analysis_method': extracted_info.get('statistical_method', 'Not specified'),
            'detailed_methods': statistical_details
        },
        
        'study_conduct': {
            'visit_schedule': visit_schedule,
            'inclusion_criteria': criteria.get('inclusion', 'Not specified'),
            'exclusion_criteria': criteria.get('exclusion', 'Not specified')
        },
        
        'document_metadata': {
            'extraction_timestamp': str(file_path),
            'document_length': len(text_content),
            'extraction_confidence': _assess_extraction_confidence(extracted_info, sample_size_info)
        }
    }
    
    return comprehensive_analysis

def _extract_sample_size_details(text_content: str) -> dict:
    """Extract the full 'Sample Size' or 'Sample Size Determination' section as a block."""
    
    sample_info = {
        'sample_size_section': 'Not found'
    }
    
    # Look for section headers
    section_patterns = [
        r'(?i)(sample size determination|sample size)[\s\n]*[:\-]*[\s\n]*(.+?)(?=\n[A-Z][^\n]{0,60}\n|\n{2,}|\Z)',
        # Matches 'Sample Size' or 'Sample Size Determination' followed by text, until next section header or double newline or end of text
    ]
    
    for pattern in section_patterns:
        match = re.search(pattern, text_content, re.DOTALL)
        if match:
            # Return the section header and its content
            section_header = match.group(1).strip()
            section_text = match.group(2).strip()
            sample_info['sample_size_section'] = f"{section_header}\n{section_text}"
            break
    
    return sample_info

def _extract_visit_schedule(text_content: str) -> dict:
    """Extract detailed visit schedule information."""
    
    visit_patterns = [
        r'(?i)visit schedule(.{0,300})',
        r'(?i)(?:baseline|screening).{0,100}(?:week|day|month)(.{0,200})',
        r'(?i)(?:follow.?up|assessment).{0,50}(?:visit|schedule)(.{0,200})',
        r'(?i)(?:week|day|month)\s*\d+(.{0,100}visit)'
    ]
    
    visit_info = {'schedule_details': 'Not specified', 'visit_frequency': 'Not specified'}
    
    for pattern in visit_patterns:
        match = re.search(pattern, text_content, re.DOTALL)
        if match:
            visit_info['schedule_details'] = match.group(1).strip()[:400]
            break
    
    # Extract frequency
    frequency_patterns = [
        r'(?i)(?:every|each)\s*(\d+\s*(?:week|day|month)s?)',
        r'(?i)(\d+\s*(?:week|day|month)ly)',
        r'(?i)(daily|weekly|monthly|quarterly)'
    ]
    
    for pattern in frequency_patterns:
        match = re.search(pattern, text_content)
        if match:
            visit_info['visit_frequency'] = match.group(1)
            break
    
    return visit_info

def _extract_treatment_arms(text_content: str) -> list:
    """Extract treatment arm information."""
    
    arm_patterns = [
        r'(?i)(?:arm|group)\s*[a-z]?[:\s]*(.{0,100})',
        r'(?i)(?:treatment|intervention)\s*[a-z]?[:\s]*(.{0,100})',
        r'(?i)(?:experimental|control|placebo)\s*(?:arm|group)[:\s]*(.{0,100})'
    ]
    
    arms = []
    for pattern in arm_patterns:
        matches = re.finditer(pattern, text_content)
        for match in matches:
            arm_desc = match.group(1).strip()
            if len(arm_desc) > 10 and arm_desc not in arms:  # Avoid duplicates and too short descriptions
                arms.append(arm_desc[:200])  # Limit length
                if len(arms) >= 5:  # Limit number of arms
                    break
    
    return arms if arms else ['Not specified']

def _extract_inclusion_exclusion_criteria(text_content: str) -> dict:
    """Extract inclusion and exclusion criteria."""
    
    criteria = {'inclusion': 'Not specified', 'exclusion': 'Not specified'}
    
    # Inclusion criteria
    inclusion_patterns = [
        r'(?i)inclusion criteria(.{0,500}?)(?:exclusion criteria|exclusion|$)',
        r'(?i)patients.{0,50}eligible(.{0,300}?)(?:exclusion|$)',
        r'(?i)subjects.{0,50}included(.{0,300}?)(?:exclusion|$)'
    ]
    
    for pattern in inclusion_patterns:
        match = re.search(pattern, text_content, re.DOTALL)
        if match:
            criteria['inclusion'] = match.group(1).strip()[:500]
            break
    
    # Exclusion criteria  
    exclusion_patterns = [
        r'(?i)exclusion criteria(.{0,500}?)(?:\n\n|$)',
        r'(?i)patients.{0,50}excluded(.{0,300}?)(?:\n\n|$)',
        r'(?i)subjects.{0,50}excluded(.{0,300}?)(?:\n\n|$)'
    ]
    
    for pattern in exclusion_patterns:
        match = re.search(pattern, text_content, re.DOTALL)
        if match:
            criteria['exclusion'] = match.group(1).strip()[:500]
            break
    
    return criteria

def _extract_statistical_details(text_content: str) -> dict:
    """Extract the full 'Primary analysis approach' and 'Missing Data' or similar sections as blocks."""
    
    stats_details = {
        'primary_analysis_section': 'Not found',
        'missing_data_section': 'Not found',
        'secondary_analysis': 'Not specified',
        'significance_level': 'Not specified',
        'power': 'Not specified'
    }
    
    # Look for section headers for primary analysis
    primary_section_patterns = [
        r'(?i)(analysis methods for efficacy endpoints|primary analysis approach|primary analysis|statistical methods for efficacy endpoints|statistical analysis)[\s\n]*[:\-]*[\s\n]*(.+?)(?=\n[A-Z][^\n]{0,60}\n|\n{2,}|\Z)',
    ]
    for pattern in primary_section_patterns:
        match = re.search(pattern, text_content, re.DOTALL)
        if match:
            section_header = match.group(1).strip()
            section_text = match.group(2).strip()
            stats_details['primary_analysis_section'] = f"{section_header}\n{section_text}"
            break
    
    # Look for section headers for missing data handling
    missing_section_patterns = [
        r'(?i)(missing data handling|missing data|imputation methods|handling of missing data|imputation strategy)[\s\n]*[:\-]*[\s\n]*(.+?)(?=\n[A-Z][^\n]{0,60}\n|\n{2,}|\Z)',
    ]
    for pattern in missing_section_patterns:
        match = re.search(pattern, text_content, re.DOTALL)
        if match:
            section_header = match.group(1).strip()
            section_text = match.group(2).strip()
            stats_details['missing_data_section'] = f"{section_header}\n{section_text}"
            break
    
    # Keep the rest of the fields as before for now
    # (secondary_analysis, significance_level, power)
    # Optionally, you could also extract these as full sections if needed
    
    return stats_details

def _detect_phase(title: str, filename: str, study_design: str) -> str:
    """Detect clinical trial phase using improved priority logic."""
    
    detected_phase = "Unknown"
    phase_patterns = {
        'Phase I': ['phase i', 'phase 1', 'phase one', 'first-in-human', 'dose escalation'],
        'Phase II': ['phase ii', 'phase 2', 'phase two', 'proof of concept', 'dose finding'],
        'Phase III': ['phase iii', 'phase 3', 'phase three', 'pivotal', 'registration'],
        'Phase IV': ['phase iv', 'phase 4', 'phase four', 'post-marketing', 'surveillance']
    }
    
    # Priority 1: Check title
    if title and title.lower() != f"document: {filename.lower()}":
        for phase, patterns in phase_patterns.items():
            if any(pattern in title.lower() for pattern in patterns):
                detected_phase = phase
                break
    
    # Priority 2: Check filename
    if detected_phase == "Unknown":
        for phase, patterns in phase_patterns.items():
            if any(pattern in filename.lower() for pattern in patterns):
                detected_phase = phase
                break
    
    # Priority 3: Check study design
    if detected_phase == "Unknown" and study_design:
        for phase, patterns in phase_patterns.items():
            if any(pattern in study_design.lower() for pattern in patterns):
                detected_phase = phase
                break
    
    return detected_phase

def _assess_extraction_confidence(extracted_info: dict, sample_size_info: dict) -> str:
    """Assess the confidence level of the extraction."""
    
    key_fields = ['title', 'primary_endpoint', 'statistical_method', 'study_design']
    filled_fields = sum(1 for field in key_fields if extracted_info.get(field, 'Not specified') != 'Not specified')
    
    sample_size_found = sample_size_info.get('total_sample_size', 'Not specified') != 'Not specified'
    
    if filled_fields >= 3 and sample_size_found:
        return 'High'
    elif filled_fields >= 2:
        return 'Medium'
    else:
        return 'Low'

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    
    Args:
        paper_id: The ID of the paper to look for
        
    Returns:
        JSON string with paper information if found, error message if not found
    """
 
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    
    return f"There's no saved information related to paper {paper_id}."



@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    List all available topic folders in the papers directory.
    
    This resource provides a simple list of all available topic folders.
    """
    folders = []
    
    # Get all topic directories
    if os.path.exists(PAPER_DIR):
        for topic_dir in os.listdir(PAPER_DIR):
            topic_path = os.path.join(PAPER_DIR, topic_dir)
            if os.path.isdir(topic_path):
                papers_file = os.path.join(topic_path, "papers_info.json")
                if os.path.exists(papers_file):
                    folders.append(topic_dir)
    
    # Create a simple markdown list
    content = "# Available Topics\n\n"
    if folders:
        for folder in folders:
            content += f"- {folder}\n"
        content += f"\nUse @{folder} to access papers in that topic.\n"
    else:
        content += "No topics found.\n"
    
    return content

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    Get detailed information about papers on a specific topic.
    
    Args:
        topic: The research topic to retrieve papers for
    """
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPER_DIR, topic_dir, "papers_info.json")
    
    if not os.path.exists(papers_file):
        return f"# No papers found for topic: {topic}\n\nTry searching for papers on this topic first."
    
    try:
        with open(papers_file, 'r') as f:
            papers_data = json.load(f)
        
        # Create markdown content with paper details
        content = f"# Papers on {topic.replace('_', ' ').title()}\n\n"
        content += f"Total papers: {len(papers_data)}\n\n"
        
        for paper_id, paper_info in papers_data.items():
            content += f"## {paper_info['title']}\n"
            content += f"- **Paper ID**: {paper_id}\n"
            content += f"- **Authors**: {', '.join(paper_info['authors'])}\n"
            content += f"- **Published**: {paper_info['published']}\n"
            content += f"- **PDF URL**: [{paper_info['pdf_url']}]({paper_info['pdf_url']})\n\n"
            content += f"### Summary\n{paper_info['summary'][:500]}...\n\n"
            content += "---\n\n"
        
        return content
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}\n\nThe papers data file is corrupted."

@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """Generate a prompt for Claude to find and discuss academic papers on a specific topic."""
    return f"""Search for {num_papers} academic papers about '{topic}' using the search_papers tool. 

Follow these instructions:
1. First, search for papers using search_papers(topic='{topic}', max_results={num_papers})
2. For each paper found, extract and organize the following information:
   - Paper title
   - Authors
   - Publication date
   - Brief summary of the key findings
   - Main contributions or innovations
   - Methodologies used
   - Relevance to the topic '{topic}'

3. Provide a comprehensive summary that includes:
   - Overview of the current state of research in '{topic}'
   - Common themes and trends across the papers
   - Key research gaps or areas for future investigation
   - Most impactful or influential papers in this area

4. Organize your findings in a clear, structured format with headings and bullet points for easy readability.

Please present both detailed information about each paper and a high-level synthesis of the research landscape in {topic}."""

@mcp.tool()
def parse_for_index(file_path: str) -> str:
    """
    Parse a document (PDF, DOCX, DOC) and extract structured study information.
    
    Args:
        file_path: Path to the document file to parse
        
    Returns:
        JSON string with extracted study information including detected_phase,
        detected_therapeutic, and detected_indication
        
    Phase Detection Priority:
        1. Study title (most reliable)
        2. Filename 
        3. Study design field

    """
    
    # Check if file exists
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
    
    # Parse the document based on file extension
    text_content = parse_document(file_path)
    if not text_content:
        return f"Error: Could not extract text from {file_path}. Unsupported format or parsing failed."
    
    # Extract information from the text using comprehensive regex patterns
    extracted_info = {}
    
    # Define comprehensive regex patterns for extracting information
    patterns = {
        'title': [
            r'(?i)(?:title|study title):\s*(.+?)(?:\n|$)',
            r'(?i)^(.+?)\s*(?:protocol|study)',
            r'(?i)study:\s*(.+?)(?:\n|$)'
        ],
        'pharma': [
            r'(?i)(?:sponsor|pharmaceutical company|company):\s*(.+?)(?:\n|$)',
            r'(?i)(?:pharma|sponsor):\s*(.+?)(?:\n|$)'
        ],
        'study_design': [
            r'(?i)(?:study design|design):\s*(.+?)(?:\n|$)',
            r'(?i)(?:randomized|double.?blind|placebo.?controlled|crossover)[\w\s,-]+',
        ],
        'study_treatment': [
            r'(?i)(?:treatment|intervention):\s*(.+?)(?:\n|$)',
            r'(?i)(?:drug|compound|therapeutic):\s*(.+?)(?:\n|$)'
        ],
        'study_visit': [
            r'(?i)(?:visit schedule|visits):\s*(.+?)(?:\n|$)',
            r'(?i)(?:baseline|week\s+\d+|day\s+\d+|follow.?up)[\w\s,.-]+',
        ],
        'primary_analysis_endpoint': [
            r'(?i)(?:primary endpoint|primary outcome|primary analysis endpoint):\s*(.+?)(?:\n|$)',
            r'(?i)primary.{0,50}endpoint[:\s]*(.+?)(?:\n|$)'
        ],
        'primary_analysis_approach': [
            r'(?i)(?:primary analysis|statistical method|analysis approach|statistical approach):\s*(.+?)(?:\n|$)',
            r'(?i)(?:MMRM|mixed model|ANCOVA|t-test|chi-square)[\w\s()-]+',
        ],
        'sample_size': [
            r'(?i)(?:sample size|number of subjects|n\s*=):\s*(\d+)',
            r'(?i)(\d+)\s*(?:subjects|patients|participants)'
        ]
        
    }
    
    # Extract information using patterns
    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text_content)
            if match:
                extracted_info[field] = match.group(1).strip() if match.groups() else match.group(0).strip()
                break
    
    # Enhanced information extraction with document analysis
    doc_title = extracted_info.get('title', '').lower()
    doc_design = extracted_info.get('study_design', '').lower()
    doc_treatment = extracted_info.get('study_treatment', '').lower()
    
    # Create a comprehensive text for analysis
    full_text = text_content.lower()
    
    # Detect clinical trial phase
    detected_phase = "Unknown"
    phase_patterns = {
        'Phase I': ['phase i', 'phase 1', 'phase one', 'first-in-human', 'dose escalation'],
        'Phase II': ['phase ii', 'phase 2', 'phase two', 'proof of concept', 'dose finding'],
        'Phase III': ['phase iii', 'phase 3', 'phase three', 'pivotal', 'registration'],
        'Phase IV': ['phase iv', 'phase 4', 'phase four', 'post-marketing', 'surveillance']
    }
    
    # Priority 1: Check title first (most reliable)
    title_text = extracted_info.get('title', '').lower()
    if title_text and title_text != f"document: {os.path.basename(file_path).lower()}":
        for phase, patterns in phase_patterns.items():
            if any(pattern in title_text for pattern in patterns):
                detected_phase = phase
                break
    
    # Priority 2: Check filename if title didn't yield results
    if detected_phase == "Unknown":
        filename = os.path.basename(file_path).lower()
        for phase, patterns in phase_patterns.items():
            if any(pattern in filename for pattern in patterns):
                detected_phase = phase
                break
    
    # Priority 3: Check study design field (more specific than full text)
    if detected_phase == "Unknown" and doc_design:
        for phase, patterns in phase_patterns.items():
            if any(pattern in doc_design for pattern in patterns):
                detected_phase = phase
                break
    
    
    # Detect therapeutic area
    detected_therapeutic = "Unknown"
    therapeutic_mapping = {
        'Oncology': ['cancer', 'tumor', 'tumour', 'oncology', 'carcinoma', 'melanoma', 'lymphoma', 'leukemia', 'sarcoma', 'chemotherapy', 'radiation'],
        'Cardiology': ['cardiac', 'heart', 'cardiovascular', 'cardiology', 'coronary', 'myocardial', 'hypertension'],
        'Neurology': ['neurological', 'brain', 'neurology', 'alzheimer', 'parkinson', 'stroke', 'epilepsy', 'dementia'],
        'Immunology': ['immune', 'immunology', 'autoimmune', 'immunotherapy', 'rheumatoid', 'lupus'],
        'Dermatology': ['skin', 'dermatology', 'melanoma', 'dermatitis', 'psoriasis', 'eczema'],
        'Endocrinology': ['diabetes', 'diabetic', 'glucose', 'insulin', 'thyroid', 'hormone'],
        'Respiratory': ['lung', 'pulmonary', 'asthma', 'copd', 'respiratory', 'pneumonia']
    }
    
    therapeutic_scores = {}
    for area, terms in therapeutic_mapping.items():
        score = sum(3 if term in doc_design else 2 if term in doc_title else 1 if term in full_text else 0 for term in terms)
        if score > 0:
            therapeutic_scores[area] = score
    
    if therapeutic_scores:
        detected_therapeutic = max(therapeutic_scores, key=therapeutic_scores.get)
    
    # Detect indication
    detected_indication = "Unknown"
    indication_mapping = {
        'Breast Cancer': ['breast cancer', 'breast carcinoma', 'mammary carcinoma'],
        'Melanoma': ['melanoma', 'skin cancer', 'cutaneous melanoma'],
        'Lung Cancer': ['lung cancer', 'pulmonary carcinoma', 'nsclc', 'sclc', 'non-small cell', 'small cell'],
        'Heart Disease': ['heart disease', 'cardiac disease', 'myocardial infarction', 'coronary artery'],
        'Type 2 Diabetes': ['type 2 diabetes', 'diabetes mellitus', 't2dm', 'diabetic'],
        'Hypertension': ['hypertension', 'high blood pressure', 'elevated blood pressure'],
        'Alzheimer Disease': ['alzheimer', 'dementia', 'cognitive impairment'],
        'Rheumatoid Arthritis': ['rheumatoid arthritis', 'ra', 'joint inflammation']
    }
    
    indication_scores = {}
    for condition, terms in indication_mapping.items():
        score = sum(3 if term in doc_design else 2 if term in doc_title else 1 if term in full_text else 0 for term in terms)
        if score > 0:
            indication_scores[condition] = score
    
    if indication_scores:
        detected_indication = max(indication_scores, key=indication_scores.get)
    
    # Compile comprehensive study information
    study_info = {
        'title': extracted_info.get('title', f"Document: {os.path.basename(file_path)}"),
        'pharma': extracted_info.get('pharma', 'Not specified'),
        'study_design': extracted_info.get('study_design', 'Not specified'),
        'study_treatment': extracted_info.get('study_treatment', 'Not specified'),
        'study_visit': extracted_info.get('study_visit', 'Not specified'),
        'primary_analysis_endpoint': extracted_info.get('primary_analysis_endpoint', 'Not specified'),
        'primary_analysis_approach': extracted_info.get('primary_analysis_approach', 'Not specified'),
        'sample_size': extracted_info.get('sample_size', 'Not specified'),
        'imputation_method': extracted_info.get('imputation_method', 'Not specified'),
        'detected_phase': detected_phase,
        'detected_therapeutic': detected_therapeutic,
        'detected_indication': detected_indication,
        'source_file': file_path,
        'document_length': len(text_content),
        'extraction_confidence': 'High' if len([v for v in extracted_info.values() if v]) > 5 else 'Medium' if len([v for v in extracted_info.values() if v]) > 2 else 'Low'
    }
    
    return json.dumps(study_info, indent=2)

@mcp.prompt()
def document_parsing_guide(document_type: str = "clinical study") -> str:
    """Generate a comprehensive prompt for parsing clinical study documents."""
    return f"""You are tasked with parsing a {document_type} document to extract structured information. Use the parse_for_index tool to analyze the document and follow these guidelines:

## Document Analysis Instructions

### 1. Initial Assessment
- Identify the document type (SAP, protocol, CSR, etc.)
- Determine the clinical trial phase
- Identify the therapeutic area and specific indication

### 2. Key Information to Extract
**Study Identification:**
- Study title and protocol number
- Sponsor/pharmaceutical company
- Principal investigator(s)

**Study Design:**
- Study design type (randomized, double-blind, placebo-controlled, etc.)
- Treatment arms and interventions
- Study population and inclusion/exclusion criteria

**Study Conduct:**
- Visit schedule and timeline (every 3 weeks, daily, etc.)
- Sample size and randomization details
- Study duration and/or follow-up period (1-year duration, 3-month safety follow-up, etc.)

**Statistical Analysis:**
- Primary endpoint(s) and analysis approach (OS at 12 months, etc.)
- Secondary endpoints and analysis approach
- Statistical methods (MMRM, ANCOVA, etc.)
- Missing data handling/imputation methods

**Regulatory Information:**
- Clinical trial phase
- Therapeutic area classification
- Medical indication being studied

### 3. Analysis Process
1. **Use the parse_for_index tool** with the document file path
2. **Review the extracted information** for completeness and accuracy
3. **Save detailed analysis approaches in a complete paragraph, including hypotheses, effect sizes, baseline factors to adjust, etc.
4. **Identify any missing critical information** that should be manually reviewed
5. **Assess the extraction confidence level** based on the amount of structured data found

### 4. Output Format
Present the findings in a structured format:
- **Document Summary**: Brief overview of the study
- **Extracted Fields**: All successfully parsed information
- **Confidence Assessment**: Quality of extraction (High/Medium/Low)
- **Recommendations**: Suggestions for manual review if needed

### 5. Quality Checks
- Verify that phase, therapeutic area, and indication are logically consistent
- Check if sample size and statistical methods align with study design
- Ensure primary endpoints match the study objectives

Use this systematic approach to ensure comprehensive and accurate document parsing."""




@mcp.tool()
def find_studies(phase: str = "", therapeutic: str = "", indication: str = "") -> str:
    """
    Find study IDs based on phase, therapeutic area, and indication criteria.
    Use this to discover relevant studies before getting full details with search_primary_analysis.
    
    Args:
        phase: The clinical trial phase (e.g., "Phase I", "Phase II", "Phase III") - optional
        therapeutic: The therapeutic area - optional  
        indication: The medical indication being studied - optional
        
    Returns:
        JSON string with matching study IDs and basic information
    """
    
    # Check if index exists
    index_file = os.path.join(SAP_DIR, "_index", "studies_index.json")
    if not os.path.exists(index_file):
        return f"No search index found. Please run index_sap_documents first to build the search index."
    
    try:
        # Load the index
        with open(index_file, "r") as f:
            all_studies = json.load(f)
        
        # Search through indexed studies
        matching_studies = []
        
        for study_id, study_data in all_studies.items():
            detected_phase = study_data.get('detected_phase', '').lower()
            detected_therapeutic = study_data.get('detected_therapeutic', '').lower()
            detected_indication = study_data.get('detected_indication', '').lower()
            
            # Match criteria with detected information (empty criteria matches all)
            phase_match = not phase or phase.lower() in detected_phase or detected_phase in phase.lower()
            therapeutic_match = not therapeutic or therapeutic.lower() in detected_therapeutic or detected_therapeutic in therapeutic.lower()
            indication_match = not indication or indication.lower() in detected_indication or detected_indication in indication.lower()
            
            if phase_match and therapeutic_match and indication_match:
                matching_studies.append({
                    'study_id': study_id,
                    'detected_phase': study_data.get('detected_phase'),
                    'detected_therapeutic': study_data.get('detected_therapeutic'),
                    'detected_indication': study_data.get('detected_indication')
                })
        
        search_results = {
            'search_criteria': {
                'phase': phase or "Any",
                'therapeutic': therapeutic or "Any", 
                'indication': indication or "Any"
            },
            'total_matches': len(matching_studies),
            'matching_studies': matching_studies
        }
        
        return json.dumps(search_results, indent=2)
        
    except Exception as e:
        return f"Error searching studies: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')