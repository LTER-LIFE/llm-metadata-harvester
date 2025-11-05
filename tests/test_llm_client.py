import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_metadata_harvester.llm_client import LLMClient


class TestLLMClient:
    
    @patch('llm_metadata_harvester.llm_client.OpenAI')
    @patch('llm_metadata_harvester.llm_client.os.getenv')
    def test_init_openai_client(self, mock_getenv, mock_openai):
        """Test initialization of OpenAI client"""
        mock_getenv.return_value = "test_api_key"
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        client = LLMClient("gpt-4", temperature=0.5)
        
        assert client.model == "gpt-4"
        assert client.temperature == 0.5
        assert client.provider == "openai"
        assert client.client == mock_openai_instance
        mock_openai.assert_called_once_with(api_key="test_api_key")
    
    @patch('llm_metadata_harvester.llm_client.genai')
    @patch('llm_metadata_harvester.llm_client.os.getenv')
    def test_init_gemini_client(self, mock_getenv, mock_genai):
        """Test initialization of Gemini client"""
        mock_getenv.return_value = "test_api_key"
        mock_genai_instance = Mock()
        mock_genai.Client.return_value = mock_genai_instance
        
        client = LLMClient("gemini-pro", temperature=0.7)
        
        assert client.model == "gemini-pro"
        assert client.temperature == 0.7
        assert client.provider == "gemini"
        assert client.client == mock_genai_instance
        mock_genai.Client.assert_called_once_with(api_key="test_api_key")
    
    def test_init_unsupported_model(self):
        """Test initialization with unsupported model"""
        with pytest.raises(ValueError, match="Unsupported LLM: claude-3"):
            LLMClient("claude-3")
    
    @patch('llm_metadata_harvester.llm_client.genai', None)
    def test_init_gemini_without_genai_package(self):
        """Test initialization with Gemini when genai package is not available"""
        with pytest.raises(ImportError, match="google package is required"):
            LLMClient("gemini-pro")
    
    @patch('llm_metadata_harvester.llm_client.OpenAI')
    @patch('llm_metadata_harvester.llm_client.os.getenv')
    def test_chat_openai(self, mock_getenv, mock_openai):
        """Test chat functionality with OpenAI"""
        mock_getenv.return_value = "test_api_key"
        
        # Mock OpenAI client and response
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_openai_instance.chat.completions.create.return_value = mock_response
        
        client = LLMClient("gpt-4")
        messages = [{"role": "user", "content": "Hello"}]
        
        result = client.chat(messages, max_tokens=1000)
        
        assert result == "Test response"
        mock_openai_instance.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=messages,
            temperature=0.0,
            max_tokens=1000
        )
    
    @patch('llm_metadata_harvester.llm_client.genai')
    @patch('llm_metadata_harvester.llm_client.os.getenv')
    def test_chat_gemini(self, mock_getenv, mock_genai):
        """Test chat functionality with Gemini"""
        mock_getenv.return_value = "test_api_key"
        
        # Mock Gemini client and response
        mock_genai_instance = Mock()
        mock_genai.Client.return_value = mock_genai_instance
        
        mock_response = Mock()
        mock_response.text = "Gemini response"
        mock_genai_instance.models.generate_content.return_value = mock_response
        
        client = LLMClient("gemini-pro")
        messages = [{"role": "user", "content": "Hello"}]
        
        result = client.chat(messages, max_tokens=1000)
        
        assert result == "Gemini response"
        mock_genai_instance.models.generate_content.assert_called_once_with(
            model="gemini-pro",
            contents="Hello"
        )
    
    @patch('llm_metadata_harvester.llm_client.OpenAI')
    @patch('llm_metadata_harvester.llm_client.os.getenv')
    def test_chat_default_max_tokens(self, mock_getenv, mock_openai):
        """Test chat with default max_tokens"""
        mock_getenv.return_value = "test_api_key"
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"
        mock_openai_instance.chat.completions.create.return_value = mock_response
        
        client = LLMClient("gpt-4")
        messages = [{"role": "user", "content": "Hello"}]
        
        result = client.chat(messages)
        
        mock_openai_instance.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=messages,
            temperature=0.0,
            max_tokens=2000
        )
    
    @patch('llm_metadata_harvester.llm_client.OpenAI')
    @patch('llm_metadata_harvester.llm_client.os.getenv')
    def test_chat_openai_api_error(self, mock_getenv, mock_openai):
        """Test handling of OpenAI API errors"""
        mock_getenv.return_value = "test_api_key"
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.side_effect = Exception("API Error")
        
        client = LLMClient("gpt-4")
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(Exception, match="API Error"):
            client.chat(messages)
    
    @patch('llm_metadata_harvester.llm_client.genai')
    @patch('llm_metadata_harvester.llm_client.os.getenv')
    def test_chat_gemini_api_error(self, mock_getenv, mock_genai):
        """Test handling of Gemini API errors"""
        mock_getenv.return_value = "test_api_key"
        
        mock_genai_instance = Mock()
        mock_genai.Client.return_value = mock_genai_instance
        mock_genai_instance.models.generate_content.side_effect = Exception("Gemini API Error")
        
        client = LLMClient("gemini-pro")
        messages = [{"role": "user", "content": "Hello"}]
        
        with pytest.raises(Exception, match="Gemini API Error"):
            client.chat(messages)
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('llm_metadata_harvester.llm_client.OpenAI')
    def test_missing_api_key(self, mock_openai):
        """Test behavior when API key is missing"""
        mock_openai.side_effect = Exception("API key not found")
        
        with pytest.raises(Exception, match="API key not found"):
            LLMClient("gpt-4") 