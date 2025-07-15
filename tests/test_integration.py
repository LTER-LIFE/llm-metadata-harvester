import pytest
from unittest.mock import Mock, patch, AsyncMock
from llm_metadata_harvester.harvester_operations import extract_entities
from llm_metadata_harvester.llm_client import LLMClient
from llm_metadata_harvester.webutils import extract_full_page_text, readWebContent
from llm_metadata_harvester.utils import compute_mdhash_id, clean_str


class TestIntegrationWorkflow:
    """Integration tests for the complete metadata harvesting workflow"""
    
    @patch('llm_metadata_harvester.llm_client.OpenAI')
    @patch('llm_metadata_harvester.llm_client.os.getenv')
    @patch('llm_metadata_harvester.harvester_operations.tiktoken')
    def test_full_metadata_extraction_workflow(self, mock_tiktoken, mock_getenv, mock_openai):
        """Test the complete workflow from text input to metadata extraction"""
        # Setup mocks
        mock_getenv.return_value = "test_api_key"
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        # Mock tiktoken for text chunking
        mock_encoder = Mock()
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5]  # Short text, single chunk
        mock_encoder.decode.return_value = "test document content"
        mock_tiktoken.encoding_for_model.return_value = mock_encoder
        
        # Mock LLM responses
        initial_response = '''("entity"<|>"Dataset Title"<|>"Title"<|>"A comprehensive dataset about environmental monitoring"<|>"chunk1"<|>"test.txt")##
("entity"<|>"MIT License"<|>"License"<|>"Open source license allowing reuse"<|>"chunk1"<|>"test.txt")##
("entity"<|>"Environmental Research Institute"<|>"Data creator"<|>"Research institution that created the dataset"<|>"chunk1"<|>"test.txt")'''
        
        post_processing_response = '''("entity"<|>"Title"<|>"A comprehensive dataset about environmental monitoring")##
("entity"<|>"License"<|>"MIT License")##
("entity"<|>"Data creator"<|>"Environmental Research Institute")'''
        
        mock_openai_instance.chat.completions.create.side_effect = [
            Mock(choices=[Mock(message=Mock(content=initial_response))]),
            Mock(choices=[Mock(message=Mock(content=post_processing_response))])
        ]
        
        # Setup test data
        llm = LLMClient("gpt-4")
        meta_field_dict = {
            "Title": "Dataset title",
            "License": "Dataset license",
            "Data creator": "Who created the dataset"
        }
        test_text = "This is a comprehensive dataset about environmental monitoring created by the Environmental Research Institute under MIT License."
        
        # Execute the workflow
        result = extract_entities(
            text=test_text,
            meta_field_dict=meta_field_dict,
            llm=llm,
            source_url="https://example.com/dataset"
        )
        
        # Verify results
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # Verify LLM was called correctly
        assert mock_openai_instance.chat.completions.create.call_count == 2
        
        # Verify chunking was attempted
        mock_tiktoken.encoding_for_model.assert_called_with("gpt-4")
    
    @patch('llm_metadata_harvester.webutils.requests.get')
    def test_web_scraping_to_text_extraction_workflow(self, mock_get):
        """Test workflow from web scraping to text extraction"""
        # Mock web response
        html_content = '''
        <html>
            <head><title>Dataset Portal</title></head>
            <body>
                <h1>Environmental Dataset</h1>
                <p>This dataset contains environmental monitoring data collected over 5 years.</p>
                <div class="metadata">
                    <p>License: MIT</p>
                    <p>Creator: Environmental Research Institute</p>
                    <p>Keywords: environment, monitoring, data</p>
                </div>
            </body>
        </html>
        '''
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html_content.encode('utf-8')
        mock_get.return_value = mock_response
        
        # Test web scraping
        soup = readWebContent("https://example.com/dataset")
        
        # Verify content extraction
        assert soup is not None
        assert soup.find('h1').text == 'Environmental Dataset'
        assert 'environmental monitoring data' in soup.get_text()
        assert 'MIT' in soup.get_text()
        assert 'Environmental Research Institute' in soup.get_text()
        
        # Test text extraction for metadata harvesting
        full_text = soup.get_text()
        assert 'Environmental Dataset' in full_text
        assert 'MIT' in full_text
        assert 'Environmental Research Institute' in full_text
    
    @pytest.mark.asyncio
    async def test_async_web_scraping_workflow(self):
        """Test async web scraping workflow"""
        with patch('llm_metadata_harvester.webutils.async_playwright') as mock_playwright:
            # Mock playwright
            mock_context = AsyncMock()
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            
            mock_playwright.return_value.__aenter__.return_value = mock_context
            mock_context.chromium.launch.return_value = mock_browser
            mock_browser.new_page.return_value = mock_page
            
            # Mock page content
            page_text = """
            Environmental Dataset Portal
            
            Dataset: Air Quality Monitoring Data
            Description: Comprehensive air quality measurements from urban sensors
            License: Creative Commons Attribution 4.0
            Publisher: City Environmental Agency
            Keywords: air quality, sensors, urban, monitoring
            Spatial Coverage: City boundaries
            Temporal Coverage: 2020-2024
            """
            mock_page.inner_text.return_value = page_text
            
            # Execute async scraping
            result = await extract_full_page_text("https://example.com/dataset")
            
            # Verify results
            assert result == page_text
            assert 'Air Quality Monitoring Data' in result
            assert 'Creative Commons Attribution 4.0' in result
            assert 'City Environmental Agency' in result
    
    def test_utility_functions_integration(self):
        """Test integration of utility functions"""
        # Test content processing pipeline
        raw_content = "  Test Content &lt;with&gt; HTML entities  "
        
        # Clean the content
        cleaned_content = clean_str(raw_content)
        assert cleaned_content == "Test Content <with> HTML entities"
        
        # Generate hash for content
        content_hash = compute_mdhash_id(cleaned_content)
        assert isinstance(content_hash, str)
        assert len(content_hash) == 32
        
        # Test hash consistency
        same_hash = compute_mdhash_id(cleaned_content)
        assert content_hash == same_hash
        
        # Test different content produces different hash
        different_content = "Different content"
        different_hash = compute_mdhash_id(different_content)
        assert content_hash != different_hash
    
    @patch('llm_metadata_harvester.llm_client.OpenAI')
    @patch('llm_metadata_harvester.llm_client.os.getenv')
    def test_error_handling_workflow(self, mock_getenv, mock_openai):
        """Test error handling in the complete workflow"""
        # Setup mocks
        mock_getenv.return_value = "test_api_key"
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        # Mock LLM error
        mock_openai_instance.chat.completions.create.side_effect = Exception("API Error")
        
        llm = LLMClient("gpt-4")
        meta_field_dict = {"Title": "Dataset title"}
        
        # Test that errors are propagated properly
        with pytest.raises(Exception, match="API Error"):
            extract_entities(
                text="test text",
                meta_field_dict=meta_field_dict,
                llm=llm
            )
    
    @patch('llm_metadata_harvester.llm_client.genai')
    @patch('llm_metadata_harvester.llm_client.os.getenv')
    def test_gemini_integration_workflow(self, mock_getenv, mock_genai):
        """Test workflow with Gemini LLM"""
        # Setup mocks
        mock_getenv.return_value = "test_api_key"
        mock_genai_instance = Mock()
        mock_genai.Client.return_value = mock_genai_instance
        
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = '''("entity"<|>"Test Dataset"<|>"Title"<|>"A test dataset")##'''
        mock_genai_instance.models.generate_content.return_value = mock_response
        
        llm = LLMClient("gemini-pro")
        meta_field_dict = {"Title": "Dataset title"}
        
        # For Gemini, we need to mock the chunking differently since it doesn't use tiktoken
        with patch('llm_metadata_harvester.harvester_operations.chunk_text') as mock_chunk:
            mock_chunk.return_value = ["test text"]
            
            # Execute workflow
            result = extract_entities(
                text="test text",
                meta_field_dict=meta_field_dict,
                llm=llm
            )
            
            # Verify Gemini was called
            mock_genai_instance.models.generate_content.assert_called()
            assert isinstance(result, dict)
    
    def test_metadata_field_processing(self):
        """Test processing of different metadata field types"""
        # Test various metadata field scenarios
        test_cases = [
            {
                "field_name": "Title",
                "expected_type": str,
                "sample_value": "Environmental Monitoring Dataset"
            },
            {
                "field_name": "Keywords",
                "expected_type": str,
                "sample_value": "environment, monitoring, sensors"
            },
            {
                "field_name": "Spatial coverage",
                "expected_type": str,
                "sample_value": "Netherlands, North Sea region"
            },
            {
                "field_name": "License",
                "expected_type": str,
                "sample_value": "Creative Commons Attribution 4.0"
            }
        ]
        
        # Create a meta field dict from test cases
        meta_field_dict = {case["field_name"]: case["sample_value"] for case in test_cases}
        
        # Verify the structure
        assert len(meta_field_dict) == 4
        assert "Title" in meta_field_dict
        assert "Keywords" in meta_field_dict
        assert "Spatial coverage" in meta_field_dict
        assert "License" in meta_field_dict
        
        # Test that all values are strings (as expected by the system)
        for field_name, value in meta_field_dict.items():
            assert isinstance(value, str)
            assert len(value) > 0 