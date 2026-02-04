"""
LLM Client using AWS Bedrock - REAL IMPLEMENTATION
"""
import json
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
from config import settings


class BedrockLLMClient:
    """LLM client using AWS Bedrock with Meta Llama 3.3 70B"""
    
    def __init__(self):
        """Initialize Bedrock client"""
        self.mock_mode = False
        
        try:
            # Initialize boto3 client for Bedrock Runtime
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
            
            # Test connection by listing models
            try:
                response = self.bedrock_runtime.list_foundation_models()
                print(f"✅ Bedrock connected! Found {len(response.get('modelSummaries', []))} models")
                print(f"✅ Using model: {settings.bedrock_model_id}")
            except Exception as e:
                print(f"⚠️  Bedrock connection test failed: {e}")
                print(f"⚠️  Will attempt to use model anyway...")
                
        except Exception as e:
            print(f"❌ Bedrock initialization failed: {e}")
            print(f"❌ FALLING BACK TO MOCK MODE")
            print(f"❌ Add valid AWS credentials to backend/.env or run Terraform setup")
            self.bedrock_runtime = None
            self.mock_mode = True
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 4096) -> str:
        """
        Get text completion from LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLM response as string
        """
        if self.mock_mode or not self.bedrock_runtime:
            return self._mock_response(prompt)
        
        try:
            print(f"🔍 Calling {settings.bedrock_model_id[:40]}... (max_tokens={max_tokens})")
            
            # Detect model type from ID
            model_id = settings.bedrock_model_id
            
            if "anthropic" in model_id or "claude" in model_id:
                # Anthropic Claude format
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": settings.bedrock_model_temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
                if system_prompt:
                    request_body["system"] = system_prompt
                    
            elif "meta" in model_id or "llama" in model_id:
                # Meta Llama format
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"
                request_body = {
                    "prompt": full_prompt,
                    "temperature": settings.bedrock_model_temperature,
                    "max_gen_len": max_tokens,
                }
            else:
                # Generic format - try Anthropic style
                request_body = {
                    "max_tokens": max_tokens,
                    "temperature": settings.bedrock_model_temperature,
                    "messages": [{"role": "user", "content": prompt}]
                }
                if system_prompt:
                    request_body["system"] = system_prompt
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=settings.bedrock_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            print(f"✅ Got response!")
            
            # Extract text from response - handle multiple formats
            # Anthropic Claude format
            if 'content' in response_body and isinstance(response_body['content'], list):
                return response_body['content'][0]['text']
            # Meta Llama format
            elif 'generation' in response_body:
                return response_body['generation']
            # OpenAI-style format
            elif 'choices' in response_body:
                return response_body['choices'][0]['message']['content']
            # Simple content field
            elif 'content' in response_body:
                return response_body['content']
            # Completion field
            elif 'completion' in response_body:
                return response_body['completion']
            # Output wrapper
            elif 'output' in response_body:
                if isinstance(response_body['output'], dict) and 'message' in response_body['output']:
                    return response_body['output']['message']['content']
                return response_body['output']
            else:
                print(f"⚠️  Unexpected response format: {response_body}")
                return str(response_body)
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            print(f"❌ Bedrock API Error ({error_code}): {error_msg}")
            
            if error_code == 'AccessDeniedException':
                print(f"❌ ACCESS DENIED! You need to:")
                print(f"   1. Request model access in AWS Console")
                print(f"   2. Go to: https://console.aws.amazon.com/bedrock")
                print(f"   3. Click 'Model Access' → Enable DeepSeek")
            elif error_code == 'ResourceNotFoundException':
                print(f"❌ MODEL NOT FOUND! Model ID might be wrong:")
                print(f"   Current: {settings.bedrock_model_id}")
                print(f"   Try: anthropic.claude-3-sonnet-20240229-v1:0")
            
            print(f"❌ Falling back to mock mode")
            self.mock_mode = True
            return self._mock_response(prompt)
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print(f"❌ Falling back to mock mode")
            self.mock_mode = True
            return self._mock_response(prompt)
    
    def complete_json(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 4096) -> Dict[str, Any]:
        """
        Get JSON completion from LLM
        
        Args:
            prompt: User prompt (should instruct to output JSON)
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Parsed JSON as dictionary
        """
        # Add JSON instruction to system prompt
        json_instruction = """You MUST output ONLY valid JSON. 
No explanations, no markdown, no code blocks, just pure JSON.
Start directly with { or [ and end with } or ]."""
        
        if system_prompt:
            system_prompt = f"{system_prompt}\n\n{json_instruction}"
        else:
            system_prompt = json_instruction
        
        # Add JSON reminder to prompt
        if "output only" not in prompt.lower():
            prompt = f"{prompt}\n\nIMPORTANT: Output ONLY valid JSON. No markdown, no explanations."
        
        response_text = self.complete(prompt, system_prompt, max_tokens=max_tokens)
        
        # Clean response
        response_text = self._clean_json_response(response_text)
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Response was: {response_text[:500]}")
            return self._extract_json(response_text)
    
    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks if present"""
        text = text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        return text.strip()
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Try to extract JSON from text that might contain other content"""
        import re
        
        # Try to find JSON object or array
        # Match { ... } or [ ... ]
        json_pattern = r'(\{(?:[^{}]|(?:\{[^{}]*\}))*\}|\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\])'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
        
        # If still failed, return error
        return {
            "error": "Failed to parse JSON from LLM response",
            "raw_response": text[:500],
            "suggestion": "The model might not be outputting valid JSON. Check model configuration."
        }
    
    def _mock_response(self, prompt: str) -> str:
        """Mock response for development without AWS Bedrock"""
        print(f"⚠️  MOCK MODE: Returning fake data")
        print(f"⚠️  To use real AI, add AWS credentials to backend/.env")
        
        if "contribution" in prompt.lower():
            return json.dumps([
                {
                    "contribution_type": "⚠️ MOCK - Novel Architecture",
                    "specific_innovation": "This is a MOCK response. Add AWS Bedrock credentials to .env to use real AI analysis.",
                    "problem_addressed": "Testing the application without AWS credentials configured",
                    "evidence_location": "Development Mode - No Real Analysis",
                    "comment": "Run Terraform setup or add AWS credentials to backend/.env"
                },
                {
                    "contribution_type": "⚠️ MOCK - Training Procedure",
                    "specific_innovation": "Configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in backend/.env",
                    "problem_addressed": "Application is running in mock mode for development",
                    "evidence_location": "See terraform/ folder for AWS setup",
                    "comment": "Request Bedrock model access in AWS Console"
                }
            ])
        elif "experiment" in prompt.lower():
            return json.dumps({
                "experiments": [{
                    "experiment_id": "mock_exp",
                    "name": "⚠️ MOCK Experiment - Configure AWS Bedrock",
                    "description": "This is a mock response. Add AWS credentials to backend/.env for real analysis.",
                    "task": "Setup Required",
                    "datasets": [{"name": "Run: cd terraform && terraform apply"}],
                    "baselines": [{"name": "Then add credentials to backend/.env"}],
                    "proposed_methods": [{"name": "Restart backend server"}],
                    "evaluation_metrics": [{"name": "Real AI analysis will work!"}],
                    "results": [],
                    "hyperparameters": {},
                    "evidence_location": "Mock Mode",
                    "notes": "See terraform/README.md for setup instructions"
                }]
            })
        else:
            return """⚠️ MOCK MODE ACTIVE

This is a mock response because AWS Bedrock credentials are not configured.

To enable real AI analysis:
1. Run Terraform setup: cd terraform && terraform apply
2. Copy credentials to backend/.env
3. Request model access in AWS Console
4. Restart backend server

See terraform/README.md for detailed instructions."""


# Global LLM client instance
_llm_client = None


def get_llm_client():
    """Get or create global LLM client instance based on settings"""
    global _llm_client
    if _llm_client is None:
        from config import settings
        from .deepseek_client import DeepSeekClient
        
        if settings.llm_provider.lower() == "deepseek":
            print(f"🔧 Using DeepSeek LLM (provider={settings.llm_provider})")
            _llm_client = DeepSeekClient(api_key=settings.deepseek_api_key)
        else:
            print(f"🔧 Using Bedrock LLM (provider={settings.llm_provider})")
            _llm_client = BedrockLLMClient()
    return _llm_client
