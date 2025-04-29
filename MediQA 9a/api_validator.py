"""
API Validator Service

This module provides utilities to validate external API connections
and handle API errors gracefully with appropriate feedback.
"""

import logging
import requests
import json
from config import MISTRAL_API_KEY

logger = logging.getLogger(__name__)

def validate_mistral_api():
    """
    Validate that the Mistral API key is working properly.
    
    Returns:
        tuple: (is_valid, message)
            is_valid (bool): Whether the API key is valid and API is accessible
            message (str): A message describing the validation result
    """
    # Check if API key is set to a valid-looking value
    if MISTRAL_API_KEY in ["YOUR_MISTRAL_API_KEY", "", None]:
        logger.warning("Mistral API key not configured")
        return False, "API key not configured. Please provide a valid Mistral API key."
    
    # Test endpoint with minimal payload
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MISTRAL_API_KEY}"
    }
    
    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"}
        ],
        "temperature": 0.7,
        "max_tokens": 10
    }
    
    try:
        # Make a test request with short timeout
        logger.info("Testing Mistral API connection")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        # Check response status
        if response.status_code == 200:
            try:
                # Verify we can parse the response
                response_json = response.json()
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    logger.info("Mistral API validation successful")
                    return True, "API connection verified successfully"
                else:
                    logger.warning("Mistral API returned unexpected data structure")
                    return False, "API returned unexpected data structure"
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Mistral API response: {response.text[:100]}")
                return False, "Failed to parse API response"
        elif response.status_code == 401:
            logger.error("Mistral API unauthorized: Invalid API key")
            return False, "Invalid API key. Please check your Mistral API key."
        elif response.status_code == 403:
            logger.error("Mistral API forbidden: Authentication error")
            return False, "API authentication error. Please check your Mistral API key permissions."
        else:
            logger.error(f"Mistral API error: Status {response.status_code}")
            return False, f"API error: Status code {response.status_code}"
    except requests.exceptions.Timeout:
        logger.error("Mistral API request timed out")
        return False, "API request timed out. Service may be temporarily unavailable."
    except requests.exceptions.ConnectionError:
        logger.error("Mistral API connection error")
        return False, "Could not connect to API. Please check your internet connection."
    except Exception as e:
        logger.error(f"Unexpected error testing Mistral API: {e}")
        return False, f"Unexpected error: {str(e)}"

def get_api_status():
    """
    Get status of all external APIs used by the application.
    
    Returns:
        dict: API status information
            {
                'mistral': {
                    'status': bool,
                    'message': str
                },
                ...
            }
    """
    status = {}
    
    # Check Mistral API
    mistral_valid, mistral_message = validate_mistral_api()
    status['mistral'] = {
        'status': mistral_valid,
        'message': mistral_message
    }
    
    # Add more API validations here as needed
    
    return status