"""
The code in this file are partally copied or based on lightRAG project ->
https://github.com/HKUDS/LightRAG?

Following the  MIT License:

Copyright (c) 2025 LightRAG Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from llm_metadata_harvester.utils import (
    logger,
    clean_str,
    compute_mdhash_id,
    is_float_regex,
    normalize_extracted_info,
    split_string_by_multi_markers,
)
from collections import defaultdict
from llm_metadata_harvester.cheatsheet import CHEATSHEETS
from llm_metadata_harvester.prompt import PROMPTS

import tiktoken
import re

from functools import wraps
from llm_metadata_harvester.llm_client import LLMClient


def chunk_text(text: str,
               llm: LLMClient,
               max_tokens: int = 6000) -> list[str]:
    """Split text into chunks that fit within token limit"""
    chunks = []
    
    if llm.provider == "openai":
        encoder = tiktoken.encoding_for_model(llm.model)
        tokens = encoder.encode(text)
        
        current_chunk = []
        current_length = 0
        
        for token in tokens:
            if current_length + 1 > max_tokens:
                # Convert chunk back to text
                chunk_text = encoder.decode(current_chunk)
                chunks.append(chunk_text)
                current_chunk = []
                current_length = 0
            
            current_chunk.append(token)
            current_length += 1
        
        if current_chunk:
            chunks.append(encoder.decode(current_chunk))
    
    else:
        # For non-OpenAI models, use character-based chunking
        # Assuming average of 4 characters per token
        char_limit = max_tokens * 4
        
        for i in range(0, len(text), char_limit):
            chunk = text[i:i + char_limit]
            # Try to break at sentence boundary
            if i + char_limit < len(text):
                last_period = chunk.rfind('.')
                if last_period > 0:
                    chunks.append(chunk[:last_period + 1])
                    text = text[i + last_period + 1:]
                else:
                    chunks.append(chunk)
            else:
                chunks.append(chunk)
    
    return chunks

def _get_nightly_entity_template(meta_field_dict: dict) -> str:
    line_template = '("entity"{tuple_delimiter}"<Nightly Entity Name>"{tuple_delimiter}"{field_name}"{tuple_delimiter}"<Nightly Inference>"){record_delimiter}'
    template = ""
    for field_name in meta_field_dict.keys():
        template += line_template.format(
            record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
            tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
            field_name=field_name,
        )
    return template



def extract_entities(text: str,
                     meta_field_dict: dict = None,
                     llm: LLMClient = None,
                     source_url: str = "",
                     return_initial_result: bool = False) -> dict | tuple[dict, dict]:
    """
    Extract entities and relationships from text using LLM.
    Args:
        text (str): The input text to process.
        meta_field_dict (dict): Dictionary of metadata fields to extract.
        llm (LLMClient): The LLM client to use for entity extraction.
        source_url (str): Optional URL for the source of the text.
        return_initial_result (bool): If True, return both initial and cleaned nodes.
    """
    # Split text into chunks
    chunks = chunk_text(text, llm, max_tokens=4000)  # Leave room for completion
    entity_types = meta_field_dict.keys()

    nightly_entities_prompt = _get_nightly_entity_template(meta_field_dict)

    all_records = []

    special_interest = ""
    for field_name, field_value in meta_field_dict.items():
        special_interest += f"{field_name}: {field_value}\n"
    
    # Process each chunk
    for chunk in chunks:
        chunk_index = chunks.index(chunk)

        formatted_prompt = {
            "language": "English",
            "tuple_delimiter": PROMPTS["DEFAULT_TUPLE_DELIMITER"],
            "record_delimiter": PROMPTS["DEFAULT_RECORD_DELIMITER"],
            "completion_delimiter": PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
            "entity_types": entity_types,
            "special_interest": special_interest,
            "nightly_entities": nightly_entities_prompt,
            "input_text": chunk
        }
        prompt_text = _format_prompt(formatted_prompt)
        messages=[
                    {
                        "role": "system",
                        "content": "You are an AI trained to extract entities (meta data fields) and relationships from text."
                    },
                    {
                        "role": "user",
                        "content": prompt_text
            }
        ]

        # Use llm client to get response
        response_text = llm.chat(messages)

        # Process the chunk results
        records = _process_extraction_result(
            response_text,
            chunk_key=compute_mdhash_id(chunk),
            file_path="unknown_source"
        )
        all_records += records
    
    source = source_url if source_url else "unknown_source"
    
    initial_nodes, cleaned_nodes = _post_processing_records(
        all_records,
        chunk_key=f"chunk_{chunk_index}",
        llm=llm,
        file_path=source
    )
    if return_initial_result:
        # Return both initial and cleaned nodes
        return initial_nodes, cleaned_nodes
    else:
        return cleaned_nodes

def _format_prompt(params: dict) -> str:
    # Format the prompt template with the provided parameters
    prompt_template = CHEATSHEETS["fill_nightly"]
    return prompt_template.format(**params)

def _handle_post_processed_entity_extraction(
    record_attributes: list[str],
    chunk_key: str,
    file_path: str = "unknown_source",
): 
    """Handle the extraction of a single entity from the record attributes.
    
    Args:
        record_attributes (list[str]): The attributes of the record to process
        chunk_key (str): The key for the chunk being processed
        file_path (str): The file path for citation
        
    Returns:
        dict: A dictionary containing the extracted entity information, or None if extraction fails
    """
    if len(record_attributes) < 3 or record_attributes[0] != '"entity"':
        return None

    # Clean and validate entity name
    entity_name = clean_str(record_attributes[1]).strip('"')
    if not entity_name.strip():
        logger.warning(
            f"Entity extraction error: empty entity name in: {record_attributes}"
        )
        return None

    # Normalize entity name
    entity_name = normalize_extracted_info(entity_name, is_entity=True)

    # Clean and validate entity type
    entity_value = clean_str(record_attributes[2]).strip('"')
    if not entity_value.strip() or entity_value.startswith('("'):
        logger.warning(
            f"Entity extraction error: invalid entity type in: {record_attributes}"
        )
        return None

    return dict(
        entity_name=entity_name,
        entity_value=entity_value,
        source_id=chunk_key,
        file_path=file_path,
    )

def _handle_single_entity_extraction(
    record_attributes: list[str],
    chunk_key: str,
    file_path: str = "unknown_source",
):
    if len(record_attributes) < 4 or record_attributes[0] != '"entity"':
        return None

    # Clean and validate entity name
    entity_name = clean_str(record_attributes[1]).strip('"')
    if not entity_name.strip():
        logger.warning(
            f"Entity extraction error: empty entity name in: {record_attributes}"
        )
        return None

    # Normalize entity name
    entity_name = normalize_extracted_info(entity_name, is_entity=True)

    # Clean and validate entity type
    entity_type = clean_str(record_attributes[2]).strip('"')
    if not entity_type.strip() or entity_type.startswith('("'):
        logger.warning(
            f"Entity extraction error: invalid entity type in: {record_attributes}"
        )
        return None

    # Clean and validate description
    entity_description = clean_str(record_attributes[3])
    entity_description = normalize_extracted_info(entity_description)

    if not entity_description.strip():
        logger.warning(
            f"Entity extraction error: empty description for entity '{entity_name}' of type '{entity_type}'"
        )
        return None

    return dict(
        entity_name=entity_name,
        entity_type=entity_type,
        description=entity_description,
        source_id=chunk_key,
        file_path=file_path,
    )


def _handle_single_relationship_extraction(
    record_attributes: list[str],
    chunk_key: str,
    file_path: str = "unknown_source",
):
    if len(record_attributes) < 5 or record_attributes[0] != '"relationship"':
        return None
    # add this record as edge
    source = clean_str(record_attributes[1])
    target = clean_str(record_attributes[2])

    # Normalize source and target entity names
    source = normalize_extracted_info(source, is_entity=True)
    target = normalize_extracted_info(target, is_entity=True)

    edge_description = clean_str(record_attributes[3])
    edge_description = normalize_extracted_info(edge_description)

    edge_keywords = clean_str(record_attributes[4]).strip('"').strip("'")
    edge_source_id = chunk_key
    weight = (
        float(record_attributes[-1].strip('"').strip("'"))
        if is_float_regex(record_attributes[-1])
        else 1.0
    )
    return dict(
        src_id=source,
        tgt_id=target,
        weight=weight,
        description=edge_description,
        keywords=edge_keywords,
        source_id=edge_source_id,
        file_path=file_path,
    )

def _post_process_single_record(record: str, context_base: dict) -> tuple[str, list[str]]:
    """Process a single record by cleaning and extracting its contents.
    
    Args:
        record (str): The record string to process
        context_base (dict): Dictionary containing delimiter configuration
        
    Returns:
        tuple: (processed_record, record_attributes) where:
            - processed_record is the cleaned record string
            - record_attributes is a list of attributes split by delimiter
    """
    # Add parentheses if they don't exist
    if not record.startswith('('):
        record = f'({record})'
    if not record.endswith(')'):
        record = f'{record})'
        
    # Extract content between parentheses
    match = re.search(r"\((.*)\)", record)
    if match is None:
        return None, []
        
    processed_record = match.group(1)
    record_attributes = split_string_by_multi_markers(
        processed_record, 
        [context_base["tuple_delimiter"]]
    )
    
    return processed_record, record_attributes

def _process_extraction_result(
        result: str, chunk_key: str, file_path: str = "unknown_source"
    ):
        """Process a single extraction result (either initial or gleaning)
        Args:
            result (str): The extraction result to process
            chunk_key (str): The chunk key for source tracking
            file_path (str): The file path for citation
        Returns:
            tuple: (nodes_dict, edges_dict) containing the extracted entities and relationships
        """
        context_base = dict(
            tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
            record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
            completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
        )
        maybe_nodes = defaultdict(list)
        maybe_edges = defaultdict(list)

        records = split_string_by_multi_markers(
            result,
            [context_base["record_delimiter"], context_base["completion_delimiter"], "\n"],
        )
        return records

def _post_processing_records(all_records: list[str],
                             chunk_key: str,
                             llm: LLMClient,
                             file_path: str = "unknown_source"):
    """Post-process records to extract entities and relationships.
    
    This function processes the extracted records, cleaning them and extracting
    entities and relationships based on predefined rules.
    
    Returns:
        tuple: (maybe_nodes, maybe_edges) where:
            - maybe_nodes is a dictionary of extracted entities
            - maybe_edges is a dictionary of extracted relationships
    """
    context_base = dict(
        tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
        record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
    )

    maybe_nodes = defaultdict(list)

    merged_records = ""
    for record in all_records:
        processed_record, record_attributes = _post_process_single_record(record, context_base)
        if processed_record is None:
            continue

        if_entities = _handle_single_entity_extraction(
            record_attributes, chunk_key="unknown_chunk", file_path="unknown_source"
        )
        if if_entities is not None:
            entity_type = if_entities["entity_type"]
            entity_description = if_entities["description"]
            entity_name = if_entities["entity_name"]
            maybe_nodes[entity_type].append(if_entities)
            continue

    for entity_type, entities in maybe_nodes.items():
        entity_type = entity_type.strip('"')
        entity_description = ""
        for entity in entities:
            entity_description += entity["entity_name"] + ". " + entity["description"]
        
        merged_records += f"(\"entity\"{context_base['tuple_delimiter']}{entity_type}{context_base['tuple_delimiter']}{entity_description}){context_base['record_delimiter']}\n"

    messages=[
        {
            "role": "system",
            "content": "You are an AI trained to extract entities (meta data fields) and relationships from text."
        },
        {
            "role": "user",
            "content": CHEATSHEETS["post_processing"].format(
                language="English",
                tuple_delimiter=context_base["tuple_delimiter"],
                record_delimiter=context_base["record_delimiter"],
                completion_delimiter=context_base["record_delimiter"],
                input_entities=merged_records,
            )
        }
    ]

    result = llm.chat(messages, max_tokens=2000)
    records = split_string_by_multi_markers(
        result,
        [context_base["record_delimiter"], context_base["completion_delimiter"], "\n"],
    )

    final_nodes = defaultdict(list)

    for record in records:
        # Add parentheses if they don't exist
        if not record.startswith('('):
            record = f'({record})'
        if not record.endswith(')'):
            record = f'{record})'
        record = re.search(r"\((.*)\)", record)
        if record is None:
            print(
                f"Record extraction error: invalid record format in: {record}"
            )
            continue
    
        record = record.group(1)
        record_attributes = split_string_by_multi_markers(
            record, [context_base["tuple_delimiter"]]
        )

        if_entities = _handle_post_processed_entity_extraction(
            record_attributes, chunk_key, file_path
        )
        if if_entities is not None:
            final_nodes[if_entities["entity_name"]].append(if_entities)
            continue

    return maybe_nodes, final_nodes