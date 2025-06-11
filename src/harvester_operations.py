from openai import OpenAI
from google import genai
from dotenv import load_dotenv
from utils import (
    logger,
    clean_str,
    compute_mdhash_id,
    decode_tokens_by_tiktoken,
    encode_string_by_tiktoken,
    is_float_regex,
    normalize_extracted_info,
    pack_user_ass_to_openai_messages,
    split_string_by_multi_markers,
    use_llm_func_with_cache,
)
from collections import defaultdict
from cheatsheet import CHEATSHEETS
from prompt import PROMPTS

import tiktoken
import re
import os

llm_model = "gemini-2.5-flash-preview-05-20"
# llm_model = "gpt-4"
load_dotenv()

use_openai, use_gemini = False, False
if llm_model.startswith("gpt"):
    use_openai = True
elif llm_model.startswith("gemini"):
    use_gemini = True

def chunk_text(text: str, max_tokens: int = 6000) -> list[str]:
    """Split text into chunks that fit within token limit"""
    chunks = []
    
    if use_openai:
        encoder = tiktoken.encoding_for_model(llm_model)
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

def extract_entities(text: str, entity_types: list[str], special_interest: str = "", is_croissant=False) -> dict:
    # Split text into chunks
    chunks = chunk_text(text, max_tokens=4000)  # Leave room for completion
    
    all_nodes = defaultdict(list)
    all_edges = defaultdict(list)

    if use_openai:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
    elif use_gemini:
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
    if is_croissant:
        # Use the croissant entity template for nightly entities
        nightly_entities_prompt = CHEATSHEETS["nightly_entity_template_croissant"].format(
            tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
            record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        )
    else:
        nightly_entities_prompt = CHEATSHEETS["nightly_entity_template"].format(
            tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
            record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
        )

    all_records = []
    
    # Process each chunk
    for chunk in chunks:
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
        if use_openai:
            response = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI trained to extract entities (meta data fields) and relationships from text."
                    },
                    {
                        "role": "user",
                        "content": _format_prompt(formatted_prompt)
                    }
                ],
                temperature=0.0,
                max_tokens=2000
            )
            response_text = response.choices[0].message.content
        elif use_gemini:
            response = client.models.generate_content(
                model=llm_model,
                contents=_format_prompt(formatted_prompt)
            )
            response_text = response.text


        # Process the chunk results
        records = _process_extraction_result(
            response_text,
            chunk_key=compute_mdhash_id(chunk),
            file_path="unknown_source"
        )
        all_records += records
    
    initial_nodes, cleaned_nodes = _post_processing_records(
        all_records,
        chunk_key="unknown_chunk", 
        file_path="unknown_source"
    )

    return initial_nodes, cleaned_nodes

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

def _post_processing_records(all_records: list[str], chunk_key: str, file_path: str = "unknown_source"):
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

    if use_openai:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
        response = client.chat.completions.create(
            model=llm_model,
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
            ],
            temperature=0.0,
            max_tokens=2000
        )

        result = response.choices[0].message.content
    elif use_gemini:
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

        response = client.models.generate_content(
            model=llm_model,
            contents=CHEATSHEETS["post_processing"].format(
                language="English",
                tuple_delimiter=context_base["tuple_delimiter"],
                record_delimiter=context_base["record_delimiter"],
                completion_delimiter=context_base["record_delimiter"],
                input_entities=merged_records,
            )
        )
        result = response.text

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