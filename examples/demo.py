"""
python3 examples/demo.py --api-key sk-xxxx --model-name gemini-2.5-flash-preview-05-20 --url https://stac.ecodatacube.eu/veg_quercus.robur_anv.eml/collection.json?.language=en --dump-format json --allow_retrying True
"""
import argparse
import os
import asyncio
from llm_metadata_harvester.harvester_operations import metadata_harvest
from llm_metadata_harvester.standards import LTER_LIFE_STANDARD


def parse_args():
    parser = argparse.ArgumentParser(description="Metadata Harvester Demo")
    parser.add_argument('--api-key', required=True, help='API key for LLM access')
    parser.add_argument('--model-name', required=True, help='Model name to use')
    parser.add_argument('--url', required=True, help='URL to harvest metadata from')
    parser.add_argument('--dump-format', default='none', choices=['none', 'json', 'yaml'], help='Output format')
    parser.add_argument('--allow_retrying', default='False', choices=['True','False'], help='Allow retrying on failure')
    return parser.parse_args()

def string_to_bool(s):
    return s.lower() == 'true'

async def main(args):
    os.environ['LLM_API_KEY'] = args.api_key
    extracted_metadata = await metadata_harvest(
        model_name=args.model_name,
        url=args.url,
        metadata_standard=LTER_LIFE_STANDARD,
        dump_format=args.dump_format,
        allow_retrying=string_to_bool(args.allow_retrying),
    )

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))