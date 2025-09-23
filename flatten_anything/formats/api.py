"""
API format ingestion for REST endpoints.
"""
import json
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse


def ingest_api(
    url: str,
    stream: bool = False,
    headers: Dict[str, str] | None = None,
    params: Dict[str, Any] | None = None,
    timeout: int = 30,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    Fetch data from API endpoint and convert to list of dictionaries.
    
    Args:
        url: API endpoint URL. Must be valid HTTP/HTTPS URL.
        stream: If True, raises NotImplementedError as API pagination is endpoint-specific.
        headers: Optional HTTP headers for the request.
        params: Optional query parameters for the request.
        timeout: Request timeout in seconds. Default 30.
        **kwargs: Additional arguments passed to requests.get()
                 (e.g., auth, verify, proxies, allow_redirects)
    
    Returns:
        List of dictionaries from API response. Single dict responses are wrapped in a list.
    
    Raises:
        ValueError: If URL is invalid, API request fails, response is not JSON,
                   or server returns error status code.
        NotImplementedError: If stream=True is requested.
        
    Examples:
        >>> data = ingest_api('https://api.example.com/data')
        >>> len(data)
        100
        
        >>> data = ingest_api(
        ...     'https://api.example.com/users',
        ...     headers={'Authorization': 'Bearer token'},
        ...     params={'limit': 50}
        ... )
        
    Note:
        - Follows redirects by default
        - Verifies SSL certificates by default
        - For paginated APIs, implement custom pagination logic using the API's
          specific pagination parameters (page, offset, cursor, etc.)
    """
    if stream:
        raise NotImplementedError(
            "Streaming is not directly supported for API ingestion. "
            "API pagination is endpoint-specific and requires custom implementation. "
            "For paginated APIs, implement a custom loop using the API's pagination parameters "
            "(e.g., page, offset, cursor, next_token)."
        )
    
    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(
            f"Invalid URL: {url}. "
            f"URL must include scheme (http/https) and domain."
        )
    
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(
            f"Invalid URL scheme: {parsed.scheme}. "
            f"Only HTTP and HTTPS are supported."
        )
    
    # Set sensible defaults
    headers = headers or {}
    params = params or {}
    
    # Add user agent if not specified
    if 'User-Agent' not in headers:
        headers['User-Agent'] = 'flatten-anything/1.1.0'
    
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout,
            **kwargs
        )
        
        # Check for HTTP errors
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            # Provide more context about the error
            status_code = response.status_code
            if status_code == 404:
                raise ValueError(f"API endpoint not found: {url}")
            elif status_code == 401:
                raise ValueError(f"Authentication failed for {url}. Check your credentials.")
            elif status_code == 403:
                raise ValueError(f"Access forbidden for {url}. Check your permissions.")
            elif status_code == 429:
                raise ValueError(f"Rate limit exceeded for {url}. Try again later.")
            elif status_code >= 500:
                raise ValueError(f"Server error ({status_code}) from {url}. API may be down.")
            else:
                raise ValueError(f"API request failed with status {status_code}: {e}")
        
        # Parse JSON response
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            # Provide snippet of response for debugging
            content_preview = response.text[:200]
            raise ValueError(
                f"API response is not valid JSON. "
                f"Response started with: {content_preview}... "
                f"Error: {e}"
            )
        
        # Ensure we always return a list
        if data is None:
            return []
        elif isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            # Handle primitive responses (string, number, boolean)
            return [{"value": data}]
            
    except requests.Timeout:
        raise ValueError(
            f"Request timed out after {timeout} seconds. "
            f"Try increasing the timeout parameter."
        )
    except requests.ConnectionError as e:
        raise ValueError(
            f"Failed to connect to {url}. "
            f"Check your internet connection and the URL. "
            f"Error: {e}"
        )
    except requests.RequestException as e:
        # Catch-all for other requests errors
        raise ValueError(f"API request failed: {e}")
