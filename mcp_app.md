# Healthcare MCP Application Implementation Guide

Building a Claude Desktop-like Healthcare AI Assistant using mcp-agent framework

## Table of Contents
1. [Overview & Architecture](#overview--architecture)
2. [Quick Start Implementation](#quick-start-implementation)
3. [Advanced Healthcare Agent System](#advanced-healthcare-agent-system)
4. [Integration with Neo4j MCP Server](#integration-with-neo4j-mcp-server)
5. [Clinical Safety & Compliance](#clinical-safety--compliance)
6. [User Interface Options](#user-interface-options)
7. [Deployment Guide](#deployment-guide)
8. [Next Steps & Roadmap](#next-steps--roadmap)

## Overview & Architecture

### How mcp-agent Replicates Claude Desktop

Claude Desktop's orchestration pattern:
```
User Query → Claude Desktop → Claude LLM + MCP Tools → Response
```

Your healthcare app with mcp-agent:
```
User Query → Your App → mcp-agent (AugmentedLLM + MCP Servers) → Response
```

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────┐
│                Healthcare Web App                        │
├─────────────────┬──────────────────┬───────────────────┤
│   Streamlit UI  │   FastAPI REST   │   React Frontend  │
└────────┬────────┴────────┬─────────┴────────┬──────────┘
         │                 │                   │
         ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│                 mcp-agent Framework                      │
├─────────────────┬──────────────────┬───────────────────┤
│ HealthcareAgent │  ClinicalSafety  │  ParallelWorkflow │
│   - AugmentedLLM│     Wrapper      │   - Multi-agents  │
│   - Context Mgmt│  - Safety Rules  │   - Coordination  │
└────────┬────────┴──────────┬───────┴────────┬──────────┘
         │                   │                 │
         ▼                   ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│                    MCP Servers                           │
├─────────────────┬──────────────────┬───────────────────┤
│  neo4j-ehr      │  clinical-rules  │  drug-interactions│
│  (Your server)  │   (Future)       │     (Future)      │
└─────────────────┴──────────────────┴───────────────────┘
```

## Quick Start Implementation

### 1. Installation & Dependencies

```bash
# Create project directory
mkdir healthcare-mcp-client
cd healthcare-mcp-client

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install mcp-agent anthropic streamlit python-dotenv
```

### 2. Basic Healthcare Agent

Create `healthcare_agent.py`:

```python
import asyncio
import os
from dotenv import load_dotenv
from mcp_agent import Agent, AugmentedLLM
from anthropic import Anthropic

load_dotenv()

class HealthcareAssistant:
    def __init__(self):
        # Initialize Anthropic client
        self.anthropic_client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        # Create healthcare-aware LLM
        self.augmented_llm = AugmentedLLM(
            llm_client=self.anthropic_client,
            system_prompt=self.get_healthcare_system_prompt()
        )
        
        # Create agent with your Neo4j MCP server
        self.agent = Agent(
            llm=self.augmented_llm,
            mcp_servers={
                "neo4j_ehr": {
                    "command": "/Users/samuelthio/projects/neo4j-mcp/.venv/bin/mcp-server-neo4j-ehr",
                    "args": [],
                    "cwd": "/Users/samuelthio/projects/neo4j-mcp",
                    "env": {
                        "NEO4J_URI": os.getenv("NEO4J_URI"),
                        "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
                        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
                        "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE"),
                        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
                    }
                }
            }
        )
    
    def get_healthcare_system_prompt(self):
        return """You are a healthcare AI assistant with access to electronic health record data.

IMPORTANT GUIDELINES:
- Always prioritize patient safety and privacy
- Provide evidence-based information when possible
- Flag critical values or urgent findings immediately
- Explain medical terminology clearly
- Include relevant context from patient history
- Never provide definitive diagnoses - support clinical decision-making
- Always recommend consulting with healthcare providers for medical decisions

AVAILABLE TOOLS:
You have access to EHR tools that can:
- Retrieve patient records and clinical notes
- Search discharge summaries and radiology reports
- List diagnoses, medications, lab results, and procedures
- Answer complex medical queries using natural language

When using tools:
1. Start with patient context if provided
2. Use the most appropriate tool for the query
3. Interpret results in clinical context
4. Highlight any concerning findings
5. Suggest next steps when appropriate"""

    async def chat(self, message: str, patient_id: str = None) -> str:
        """Main chat interface"""
        # Add patient context if provided
        if patient_id:
            context_message = f"Current patient ID: {patient_id}\n\nQuery: {message}"
        else:
            context_message = message
        
        try:
            # Agent automatically handles tool discovery and execution
            response = await self.agent.run(context_message)
            return response.content
        except Exception as e:
            return f"I encountered an error: {str(e)}. Please try rephrasing your question."

# Example usage
async def main():
    assistant = HealthcareAssistant()
    
    # Test basic functionality
    response = await assistant.chat(
        "What are the recent lab results for patient 10461137?",
        patient_id="10461137"
    )
    print("Assistant:", response)

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Environment Configuration

Create `.env` file:

```env
# Anthropic API Key
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Neo4j Configuration (same as your existing setup)
NEO4J_URI=neo4j+s://59e8b04a.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# OpenAI API Key (for your neo4j server's natural language features)
OPENAI_API_KEY=secret key 
```

## Advanced Healthcare Agent System

### 1. Multi-Agent Clinical Decision Support

```python
from mcp_agent.workflows import ParallelWorkflow
from typing import List, Dict, Any

class ClinicalDecisionSystem:
    """Multi-agent system for comprehensive clinical assessment"""
    
    def __init__(self):
        # Specialized agents for different clinical domains
        self.diagnostic_agent = self.create_diagnostic_agent()
        self.medication_agent = self.create_medication_agent()
        self.lab_analyst_agent = self.create_lab_analyst_agent()
        self.synthesis_agent = self.create_synthesis_agent()
    
    def create_diagnostic_agent(self):
        """Agent focused on differential diagnosis"""
        llm = AugmentedLLM(
            llm_client=Anthropic(),
            system_prompt="""You are a diagnostic specialist AI. Focus on:
            - Analyzing symptoms and clinical findings
            - Generating differential diagnoses
            - Identifying red flags requiring immediate attention
            - Recommending diagnostic workup
            
            Use available EHR tools to gather comprehensive patient history."""
        )
        
        return Agent(
            llm=llm,
            mcp_servers={"neo4j_ehr": self.get_neo4j_config()}
        )
    
    def create_medication_agent(self):
        """Agent focused on medication review and interactions"""
        llm = AugmentedLLM(
            llm_client=Anthropic(),
            system_prompt="""You are a clinical pharmacist AI. Focus on:
            - Reviewing current medications
            - Identifying drug interactions
            - Assessing appropriateness of dosing
            - Recommending medication adjustments
            
            Always consider patient allergies and contraindications."""
        )
        
        return Agent(
            llm=llm,
            mcp_servers={"neo4j_ehr": self.get_neo4j_config()}
        )
    
    def create_lab_analyst_agent(self):
        """Agent focused on laboratory result interpretation"""
        llm = AugmentedLLM(
            llm_client=Anthropic(),
            system_prompt="""You are a laboratory medicine specialist AI. Focus on:
            - Interpreting lab results in clinical context
            - Identifying trends over time
            - Flagging critical values
            - Suggesting additional testing if needed
            
            Consider patient age, gender, and clinical condition."""
        )
        
        return Agent(
            llm=llm,
            mcp_servers={"neo4j_ehr": self.get_neo4j_config()}
        )
    
    def create_synthesis_agent(self):
        """Agent that synthesizes multiple specialist opinions"""
        llm = AugmentedLLM(
            llm_client=Anthropic(),
            system_prompt="""You are a chief medical officer AI responsible for synthesizing
            multiple specialist assessments into a cohesive clinical plan.
            
            Your role:
            - Integrate different specialist perspectives
            - Identify areas of agreement and disagreement
            - Prioritize recommendations by urgency and importance
            - Create a unified action plan
            - Highlight any safety concerns"""
        )
        
        return Agent(llm=llm, mcp_servers={})  # No direct MCP access - works with synthesized data
    
    async def comprehensive_assessment(
        self, 
        patient_id: str, 
        clinical_question: str
    ) -> Dict[str, Any]:
        """Run comprehensive multi-agent assessment"""
        
        # Prepare query for each specialist
        specialist_query = f"""
        Patient ID: {patient_id}
        Clinical Question: {clinical_question}
        
        Please provide your specialized assessment based on available EHR data.
        """
        
        # Run parallel assessments
        print("🔄 Running parallel specialist consultations...")
        workflow = ParallelWorkflow([
            self.diagnostic_agent,
            self.medication_agent,
            self.lab_analyst_agent
        ])
        
        specialist_results = await workflow.run(specialist_query)
        
        # Synthesize results
        print("🧠 Synthesizing specialist opinions...")
        synthesis_prompt = f"""
        Synthesize these specialist assessments for patient {patient_id}:
        
        DIAGNOSTIC ASSESSMENT:
        {specialist_results[0]}
        
        MEDICATION REVIEW:
        {specialist_results[1]}
        
        LABORATORY ANALYSIS:
        {specialist_results[2]}
        
        Provide a unified clinical assessment with prioritized recommendations.
        """
        
        synthesis = await self.synthesis_agent.run(synthesis_prompt)
        
        return {
            "patient_id": patient_id,
            "clinical_question": clinical_question,
            "specialist_assessments": {
                "diagnostic": specialist_results[0],
                "medication": specialist_results[1],
                "laboratory": specialist_results[2]
            },
            "unified_assessment": synthesis.content,
            "timestamp": "2024-01-01T00:00:00Z"  # Add current timestamp
        }
    
    def get_neo4j_config(self):
        """Neo4j MCP server configuration"""
        return {
            "command": "/Users/samuelthio/projects/neo4j-mcp/.venv/bin/mcp-server-neo4j-ehr",
            "args": [],
            "cwd": "/Users/samuelthio/projects/neo4j-mcp",
            "env": {
                "NEO4J_URI": os.getenv("NEO4J_URI"),
                "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"), 
                "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
                "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE"),
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
            }
        }

# Example usage
async def demo_multi_agent():
    system = ClinicalDecisionSystem()
    
    result = await system.comprehensive_assessment(
        patient_id="10461137",
        clinical_question="Patient presents with shortness of breath. What's the differential diagnosis and recommended workup?"
    )
    
    print("🏥 COMPREHENSIVE CLINICAL ASSESSMENT")
    print(f"Patient: {result['patient_id']}")
    print(f"Question: {result['clinical_question']}")
    print("\n" + "="*60)
    print(result['unified_assessment'])
```

### 2. Clinical Safety Wrapper

```python
import re
import json
from typing import Dict, Any, List
from datetime import datetime

class ClinicalSafetyWrapper:
    """Wraps mcp-agent with healthcare-specific safety checks"""
    
    def __init__(self, base_agent: Agent):
        self.agent = base_agent
        self.safety_rules = self.load_clinical_safety_rules()
        self.audit_log = []
    
    def load_clinical_safety_rules(self) -> Dict[str, Any]:
        """Load clinical safety rules and contraindications"""
        return {
            "dangerous_queries": [
                r"how to.*euthan",
                r"lethal dose",
                r"suicide.*method",
                r"how to.*kill"
            ],
            "requires_physician_review": [
                r"recommend.*medication",
                r"start.*drug",
                r"discontinue.*medication",
                r"diagnosis.*is"
            ],
            "critical_values": {
                "glucose": {"low": 70, "high": 400},
                "potassium": {"low": 3.0, "high": 5.5},
                "creatinine": {"low": 0, "high": 2.0}
            }
        }
    
    async def run_with_safety(self, query: str, patient_id: str = None) -> Dict[str, Any]:
        """Execute query with clinical safety checks"""
        
        # Pre-execution safety check
        safety_check = self.check_query_safety(query)
        if not safety_check["is_safe"]:
            return {
                "content": f"⚠️ Safety Check Failed: {safety_check['reason']}",
                "safety_blocked": True,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Execute the agent
            response = await self.agent.run(query)
            
            # Post-execution safety analysis
            enhanced_response = self.enhance_response_with_safety(response, patient_id)
            
            # Audit logging
            await self.log_interaction(query, enhanced_response, patient_id)
            
            return enhanced_response
            
        except Exception as e:
            error_response = {
                "content": f"An error occurred: {str(e)}",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
            await self.log_interaction(query, error_response, patient_id)
            return error_response
    
    def check_query_safety(self, query: str) -> Dict[str, Any]:
        """Pre-execution safety checks"""
        query_lower = query.lower()
        
        # Check for dangerous content
        for pattern in self.safety_rules["dangerous_queries"]:
            if re.search(pattern, query_lower):
                return {
                    "is_safe": False,
                    "reason": "Query contains potentially harmful content"
                }
        
        return {"is_safe": True}
    
    def enhance_response_with_safety(self, response, patient_id: str = None) -> Dict[str, Any]:
        """Add safety warnings and clinical context to response"""
        content = response.content
        warnings = []
        
        # Check if response contains medication recommendations
        for pattern in self.safety_rules["requires_physician_review"]:
            if re.search(pattern, content.lower()):
                warnings.append(
                    "⚠️ Medication recommendations require physician review"
                )
        
        # Check for critical values in lab results
        critical_findings = self.detect_critical_values(content)
        if critical_findings:
            warnings.append(
                f"🚨 CRITICAL VALUES DETECTED: {', '.join(critical_findings)}"
            )
        
        # Add standard clinical disclaimer
        if not warnings:
            warnings.append(
                "ℹ️ This information is for clinical decision support only. Always verify with current guidelines and patient-specific factors."
            )
        
        return {
            "content": content,
            "warnings": warnings,
            "patient_id": patient_id,
            "tool_calls": getattr(response, 'tool_calls', []),
            "timestamp": datetime.now().isoformat(),
            "safety_checked": True
        }
    
    def detect_critical_values(self, content: str) -> List[str]:
        """Detect critical lab values in response content"""
        critical_findings = []
        
        # Simple pattern matching for common critical values
        # In production, this would be more sophisticated
        patterns = {
            "glucose": r"glucose.*?(\d+(?:\.\d+)?)",
            "potassium": r"potassium.*?(\d+(?:\.\d+)?)",
            "creatinine": r"creatinine.*?(\d+(?:\.\d+)?)"
        }
        
        for test, pattern in patterns.items():
            matches = re.finditer(pattern, content.lower())
            for match in matches:
                value = float(match.group(1))
                ranges = self.safety_rules["critical_values"][test]
                
                if value < ranges["low"] or value > ranges["high"]:
                    critical_findings.append(f"{test}: {value}")
        
        return critical_findings
    
    async def log_interaction(self, query: str, response: Dict[str, Any], patient_id: str = None):
        """Audit log for clinical interactions"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "patient_id": patient_id,
            "response_length": len(response.get("content", "")),
            "tools_used": [tc.get("tool", "unknown") for tc in response.get("tool_calls", [])],
            "warnings_generated": len(response.get("warnings", [])),
            "safety_blocked": response.get("safety_blocked", False)
        }
        
        self.audit_log.append(log_entry)
        
        # In production, you'd write this to a proper audit database
        # For now, just keep in memory
```

## Integration with Neo4j MCP Server

### 1. Server Configuration for mcp-agent

```python
def get_neo4j_mcp_config():
    """Configuration for your existing Neo4j MCP server"""
    return {
        "neo4j_ehr": {
            # Use the executable from your virtual environment
            "command": "/Users/samuelthio/projects/neo4j-mcp/.venv/bin/mcp-server-neo4j-ehr",
            "args": [],
            "cwd": "/Users/samuelthio/projects/neo4j-mcp",
            "env": {
                "NEO4J_URI": os.getenv("NEO4J_URI"),
                "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
                "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
                "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE"),
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
            }
        }
    }

def create_healthcare_agent_with_neo4j():
    """Create agent specifically configured for your Neo4j server"""
    
    llm = AugmentedLLM(
        llm_client=Anthropic(),
        system_prompt="""You are a healthcare AI with access to a Neo4j EHR database.

AVAILABLE TOOLS (from neo4j-ehr server):
- ehr_get_clinical_notes: Retrieve discharge summaries, radiology reports by patient/admission
- ehr_patient: Get comprehensive patient record with admissions, diagnoses, etc.
- ehr_list_diagnoses: List diagnoses for patient or admission
- ehr_list_lab_events: List laboratory results
- ehr_list_medications: List medications
- ehr_list_procedures: List procedures
- ehr_natural_query: Ask complex questions in natural language
- ehr_get_schema: Get database structure

TOOL USAGE STRATEGY:
1. For specific patients: Start with ehr_patient to get overview
2. For clinical notes: Use ehr_get_clinical_notes with patient_id for radiology, admission_id for discharge
3. For complex queries: Use ehr_natural_query
4. For browsing data: Use appropriate list tools

Remember: Results are ordered by charttime DESC (most recent first) when limit=1."""
    )
    
    return Agent(
        llm=llm,
        mcp_servers=get_neo4j_mcp_config()
    )
```

### 2. Tool-Specific Helpers

```python
class Neo4jEHRHelper:
    """Helper class for common Neo4j EHR operations"""
    
    def __init__(self, agent: Agent):
        self.agent = agent
    
    async def get_patient_summary(self, patient_id: str) -> Dict[str, Any]:
        """Get comprehensive patient summary"""
        query = f"""Get a comprehensive overview of patient {patient_id} including:
        - Basic demographics and current status
        - Recent admissions and diagnoses
        - Current medications
        - Recent lab results (if any abnormal values, highlight them)
        - Recent clinical notes (discharge summaries, radiology reports)"""
        
        response = await self.agent.run(query)
        return {"patient_id": patient_id, "summary": response.content}
    
    async def analyze_symptoms(self, patient_id: str, symptoms: List[str]) -> Dict[str, Any]:
        """Analyze symptoms in context of patient history"""
        symptoms_text = ", ".join(symptoms)
        query = f"""Patient {patient_id} presents with: {symptoms_text}
        
        Please:
        1. Review their medical history for relevant context
        2. Check recent lab results that might be related
        3. Look for similar past episodes
        4. Suggest differential diagnosis considerations
        5. Recommend what additional information might be helpful"""
        
        response = await self.agent.run(query)
        return {
            "patient_id": patient_id,
            "symptoms": symptoms,
            "analysis": response.content
        }
    
    async def medication_review(self, patient_id: str) -> Dict[str, Any]:
        """Comprehensive medication review"""
        query = f"""Perform a medication review for patient {patient_id}:
        
        1. List current medications
        2. Check for potential interactions
        3. Review for duplicate therapies
        4. Consider appropriateness based on diagnoses
        5. Flag any missing indicated medications based on conditions"""
        
        response = await self.agent.run(query)
        return {
            "patient_id": patient_id,
            "medication_review": response.content
        }
```

## User Interface Options

### 1. Streamlit Web App (Recommended for Quick Start)

Create `streamlit_app.py`:

```python
import streamlit as st
import asyncio
from healthcare_agent import HealthcareAssistant
from clinical_safety import ClinicalSafetyWrapper

st.set_page_config(
    page_title="Healthcare AI Assistant",
    page_icon="🏥",
    layout="wide"
)

class HealthcareStreamlitApp:
    def __init__(self):
        if 'assistant' not in st.session_state:
            st.session_state.assistant = None
        if 'messages' not in st.session_state:
            st.session_state.messages = []
    
    async def initialize_assistant(self):
        """Initialize the healthcare assistant"""
        if st.session_state.assistant is None:
            with st.spinner("🔄 Connecting to EHR systems..."):
                base_agent = HealthcareAssistant().agent
                st.session_state.assistant = ClinicalSafetyWrapper(base_agent)
    
    def run(self):
        """Main Streamlit app"""
        st.title("🏥 Healthcare AI Assistant")
        st.markdown("*Powered by mcp-agent + Neo4j EHR*")
        
        # Sidebar for patient context
        with st.sidebar:
            st.header("Patient Context")
            patient_id = st.text_input("Patient ID", placeholder="e.g., 10461137")
            
            if patient_id:
                st.success(f"Active Patient: {patient_id}")
            
            st.markdown("---")
            st.markdown("### Quick Actions")
            
            if st.button("📋 Patient Summary") and patient_id:
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"Give me a comprehensive summary of patient {patient_id}"
                })
                st.rerun()
            
            if st.button("🧪 Recent Lab Results") and patient_id:
                st.session_state.messages.append({
                    "role": "user", 
                    "content": f"What are the most recent lab results for patient {patient_id}? Highlight any abnormal values."
                })
                st.rerun()
            
            if st.button("📄 Latest Discharge Summary") and patient_id:
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"Show me the most recent discharge summary for patient {patient_id}"
                })
                st.rerun()
        
        # Main chat interface
        self.render_chat_interface(patient_id)
    
    def render_chat_interface(self, patient_id: str):
        """Render the main chat interface"""
        
        # Initialize assistant
        asyncio.run(self.initialize_assistant())
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Show warnings if present
                if "warnings" in message:
                    for warning in message["warnings"]:
                        st.warning(warning)
                
                # Show tools used
                if "tool_calls" in message and message["tool_calls"]:
                    with st.expander("🔧 Tools Used"):
                        for tool_call in message["tool_calls"]:
                            st.code(f"Tool: {tool_call.get('tool', 'unknown')}")
                            if tool_call.get('arguments'):
                                st.json(tool_call['arguments'])
        
        # Chat input
        if prompt := st.chat_input("Ask about patient care..."):
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Analyzing..."):
                    response = asyncio.run(
                        st.session_state.assistant.run_with_safety(
                            prompt, 
                            patient_id=patient_id
                        )
                    )
                
                st.markdown(response["content"])
                
                # Show warnings
                if response.get("warnings"):
                    for warning in response["warnings"]:
                        st.warning(warning)
                
                # Show tools used
                if response.get("tool_calls"):
                    with st.expander("🔧 Tools Used"):
                        for tool_call in response["tool_calls"]:
                            st.code(f"Tool: {tool_call.get('tool', 'unknown')}")
                
                # Add to message history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["content"],
                    "warnings": response.get("warnings", []),
                    "tool_calls": response.get("tool_calls", [])
                })

# Run the app
if __name__ == "__main__":
    app = HealthcareStreamlitApp()
    app.run()
```

Run with:
```bash
streamlit run streamlit_app.py
```

### 2. FastAPI REST API (for Production)

Create `api_server.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import asyncio
from healthcare_agent import HealthcareAssistant
from clinical_safety import ClinicalSafetyWrapper

app = FastAPI(title="Healthcare AI API", version="1.0.0")

# Global assistant instance
assistant = None

class ChatRequest(BaseModel):
    message: str
    patient_id: Optional[str] = None

class ChatResponse(BaseModel):
    content: str
    patient_id: Optional[str] = None
    warnings: List[str] = []
    tool_calls: List[dict] = []
    timestamp: str

@app.on_event("startup")
async def startup_event():
    """Initialize the healthcare assistant on startup"""
    global assistant
    base_agent = HealthcareAssistant().agent
    assistant = ClinicalSafetyWrapper(base_agent)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    try:
        response = await assistant.run_with_safety(
            request.message,
            patient_id=request.patient_id
        )
        
        return ChatResponse(
            content=response["content"],
            patient_id=response.get("patient_id"),
            warnings=response.get("warnings", []),
            tool_calls=response.get("tool_calls", []),
            timestamp=response["timestamp"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "healthcare-ai-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Deployment Guide

### 1. Local Development

```bash
# Clone your neo4j-mcp repository (if not already done)
git clone /path/to/neo4j-mcp
cd neo4j-mcp

# Set up the healthcare MCP client alongside it
mkdir ../healthcare-mcp-client
cd ../healthcare-mcp-client

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install mcp-agent anthropic streamlit fastapi uvicorn python-dotenv

# Copy the code files (healthcare_agent.py, clinical_safety.py, etc.)
# Set up .env file with your credentials

# Run Streamlit app
streamlit run streamlit_app.py

# Or run FastAPI server
python api_server.py
```

### 2. Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "api_server.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  healthcare-ai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - NEO4J_URI=${NEO4J_URI}
      - NEO4J_USERNAME=${NEO4J_USERNAME}
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - NEO4J_DATABASE=${NEO4J_DATABASE}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - healthcare-ai
    environment:
      - REACT_APP_API_URL=http://healthcare-ai:8000
```

### 3. Production Considerations

```python
# production_config.py
import os
from typing import Dict, Any

class ProductionConfig:
    """Production configuration for healthcare MCP app"""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        return {
            "database": {
                "audit_logs": os.getenv("AUDIT_DB_URL"),
                "encryption_key": os.getenv("ENCRYPTION_KEY")
            },
            "security": {
                "jwt_secret": os.getenv("JWT_SECRET"),
                "token_expiry": 3600,  # 1 hour
                "rate_limit": "100/hour"
            },
            "monitoring": {
                "sentry_dsn": os.getenv("SENTRY_DSN"),
                "log_level": "INFO"
            },
            "healthcare": {
                "require_physician_auth": True,
                "audit_all_interactions": True,
                "hipaa_compliance": True
            }
        }
```

## Next Steps & Roadmap

### Phase 1: Core Implementation (Week 1-2)
- [ ] Set up basic healthcare agent with mcp-agent
- [ ] Integrate with your existing Neo4j MCP server  
- [ ] Implement clinical safety wrapper
- [ ] Create Streamlit prototype
- [ ] Test basic functionality

### Phase 2: Advanced Features (Week 3-4)
- [ ] Implement multi-agent clinical decision system
- [ ] Add audit logging and compliance features
- [ ] Create FastAPI REST API
- [ ] Build React frontend (optional)
- [ ] Add user authentication

### Phase 3: Production Readiness (Week 5-6)
- [ ] Implement comprehensive error handling
- [ ] Add monitoring and alerting
- [ ] Security hardening
- [ ] Performance optimization
- [ ] Documentation and training materials

### Phase 4: Integration & Scaling (Future)
- [ ] FHIR server integration
- [ ] Epic/Cerner connectors
- [ ] Clinical decision rules engine
- [ ] Mobile app development
- [ ] Multi-tenant architecture

### Immediate Next Steps

1. **Start with the basic implementation**:
   ```bash
   pip install mcp-agent anthropic streamlit
   python healthcare_agent.py  # Test basic functionality
   ```

2. **Test with your Neo4j server**:
   - Ensure your neo4j-mcp server is working
   - Test the mcp-agent integration
   - Verify tool discovery and execution

3. **Build the Streamlit prototype**:
   - Get immediate visual feedback
   - Test different query patterns
   - Validate the user experience

4. **Add safety features incrementally**:
   - Start with basic warnings
   - Add audit logging
   - Implement clinical validation rules

### Success Metrics

- **Functionality**: Can replicate Claude Desktop's capabilities
- **Safety**: All interactions logged, warnings for critical values
- **Performance**: Response time < 5 seconds for most queries
- **Usability**: Intuitive interface for healthcare professionals
- **Compliance**: Audit trail suitable for clinical use

This implementation plan gives you a production-ready healthcare AI assistant that leverages your existing Neo4j MCP server while adding the intelligent orchestration capabilities of Claude Desktop through the mcp-agent framework.