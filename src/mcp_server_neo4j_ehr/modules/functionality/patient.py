"""Patient query functionality."""

import json
from typing import Optional
from tabulate import tabulate

from ..db_connection import Neo4jConnection
from ..data_types import Patient, Admission, Diagnosis, Procedure, Medication, LabEvent, PatientResponse, OutputFormat
from ..constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TABLE


async def get_patient(
    db: Neo4jConnection,
    subject_id: str,
    include_admissions: bool = True,
    include_diagnoses: bool = False,
    include_procedures: bool = False,
    include_medications: bool = False,
    include_lab_events: bool = False,
    format: OutputFormat = OUTPUT_FORMAT_JSON
) -> str:
    """Get comprehensive patient information."""
    
    # Build the main query
    query_parts = ["MATCH (p:Patient {subject_id: $subject_id})"]
    
    if include_admissions:
        query_parts.append("OPTIONAL MATCH (p)-[:HAS_ADMISSION]->(a:Admission)")
    
    if include_diagnoses:
        query_parts.append("OPTIONAL MATCH (a)-[:HAS_DIAGNOSIS]->(d:Diagnosis)")
    
    if include_procedures:
        query_parts.append("OPTIONAL MATCH (a)-[:HAS_PROCEDURE]->(proc:Procedure)")
    
    if include_medications:
        query_parts.append("OPTIONAL MATCH (a)-[:HAS_MEDICATION]->(m:Medication)")
    
    if include_lab_events:
        query_parts.append("OPTIONAL MATCH (a)-[:INCLUDES_LAB_EVENT]->(l:LabEvent)")
    
    # Build return statement
    return_parts = ["p"]
    if include_admissions:
        return_parts.append("COLLECT(DISTINCT a) as admissions")
    if include_diagnoses:
        return_parts.append("COLLECT(DISTINCT d) as diagnoses")
    if include_procedures:
        return_parts.append("COLLECT(DISTINCT proc) as procedures")
    if include_medications:
        return_parts.append("COLLECT(DISTINCT m) as medications")
    if include_lab_events:
        return_parts.append("COLLECT(DISTINCT l) as lab_events")
    
    query = "\n".join(query_parts) + f"\nRETURN {', '.join(return_parts)}"
    
    # Execute query
    results = await db.execute_read(query, {"subject_id": subject_id})
    
    if not results:
        return json.dumps({"error": f"Patient {subject_id} not found"})
    
    result = results[0]
    
    # Build response
    patient_data = result['p']
    # Convert Neo4j DateTime to Python datetime for patient datetime fields
    if 'dod' in patient_data and hasattr(patient_data['dod'], 'to_native'):
        patient_data['dod'] = patient_data['dod'].to_native()
    patient = Patient(**patient_data)
    
    response = PatientResponse(patient=patient)
    
    if include_admissions and 'admissions' in result:
        admissions = []
        for a in result['admissions']:
            if a:
                # Convert Neo4j DateTime to Python datetime for datetime fields
                if 'admittime' in a and hasattr(a['admittime'], 'to_native'):
                    a['admittime'] = a['admittime'].to_native()
                if 'dischtime' in a and hasattr(a['dischtime'], 'to_native'):
                    a['dischtime'] = a['dischtime'].to_native()
                if 'deathtime' in a and hasattr(a['deathtime'], 'to_native'):
                    a['deathtime'] = a['deathtime'].to_native()
                if 'edregtime' in a and hasattr(a['edregtime'], 'to_native'):
                    a['edregtime'] = a['edregtime'].to_native()
                if 'edouttime' in a and hasattr(a['edouttime'], 'to_native'):
                    a['edouttime'] = a['edouttime'].to_native()
                admissions.append(Admission(**a))
        response.admissions = admissions
    
    if include_diagnoses and 'diagnoses' in result and result['diagnoses'] is not None:
        response.diagnoses = [Diagnosis(**d) for d in result['diagnoses'] if d]
    
    if include_procedures and 'procedures' in result and result['procedures'] is not None:
        procedures = []
        for p in result['procedures']:
            if p:
                # Convert Neo4j DateTime to Python datetime for datetime fields
                if 'chartdate' in p and hasattr(p['chartdate'], 'to_native'):
                    p['chartdate'] = p['chartdate'].to_native()
                procedures.append(Procedure(**p))
        response.procedures = procedures
    
    if include_medications and 'medications' in result and result['medications'] is not None:
        medications = []
        for m in result['medications']:
            if m:
                # Convert Neo4j DateTime to Python datetime for datetime fields
                if 'verifiedtime' in m and hasattr(m['verifiedtime'], 'to_native'):
                    m['verifiedtime'] = m['verifiedtime'].to_native()
                medications.append(Medication(**m))
        response.medications = medications
    
    if include_lab_events and 'lab_events' in result and result['lab_events'] is not None:
        lab_events = []
        for l in result['lab_events']:
            if l:
                # Convert Neo4j DateTime to Python datetime for datetime fields
                if 'charttime' in l and hasattr(l['charttime'], 'to_native'):
                    l['charttime'] = l['charttime'].to_native()
                if 'storetime' in l and hasattr(l['storetime'], 'to_native'):
                    l['storetime'] = l['storetime'].to_native()
                lab_events.append(LabEvent(**l))
        response.lab_events = lab_events
    
    # Format output
    if format == OUTPUT_FORMAT_TABLE:
        return format_patient_as_table(response)
    else:
        return response.model_dump_json(exclude_none=True)


def format_patient_as_table(response: PatientResponse) -> str:
    """Format patient response as a table."""
    output = []
    
    # Patient info
    patient_info = [
        ["Subject ID", response.patient.subject_id],
        ["Gender", response.patient.gender or "N/A"],
        ["Anchor Age", response.patient.anchor_age or "N/A"],
        ["Date of Death", response.patient.dod or "N/A"]
    ]
    output.append("PATIENT INFORMATION")
    output.append(tabulate(patient_info, headers=["Field", "Value"], tablefmt="grid"))
    
    # Admissions
    if response.admissions:
        output.append("\nADMISSIONS")
        admission_data = []
        for adm in response.admissions:
            admission_data.append([
                adm.hadm_id,
                adm.admission_type,
                str(adm.admittime) if adm.admittime else "N/A",
                str(adm.dischtime) if adm.dischtime else "N/A"
            ])
        output.append(tabulate(admission_data, 
                             headers=["Admission ID", "Type", "Admit Time", "Discharge Time"],
                             tablefmt="grid"))
    
    # Similar formatting for other sections...
    
    return "\n".join(output)