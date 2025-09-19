#!/usr/bin/env python3
"""
Simple test script to verify API endpoints are working
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"


def test_endpoint(method: str, path: str, data: Dict[str, Any] = None, name: str = ""):
    """Test an API endpoint and print results."""
    url = f"{BASE_URL}{API_PREFIX}{path}"
    print(f"\n{'='*50}")
    print(f"Testing: {name or path}")
    print(f"Method: {method}")
    print(f"URL: {url}")

    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"Unsupported method: {method}")
            return

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Success!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the backend is running!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def main():
    print("\n🧪 Testing Local Mind API Endpoints")
    print("=====================================")

    # Test health check
    test_endpoint("GET", "/health", name="Health Check")

    # Test ping
    test_endpoint("GET", "/ping", name="Ping")

    # Test API info
    test_endpoint("GET", "/info", name="API Information")

    # Test chat endpoint with sample message
    test_endpoint(
        "POST",
        "/chat/",
        data={
            "message": "Hello, can you help me understand this document?",
            "include_citations": True,
            "max_results": 5,
            "temperature": 0.7
        },
        name="Chat Endpoint"
    )

    # Test search endpoint
    test_endpoint(
        "POST",
        "/search/",
        data={
            "query": "machine learning",
            "limit": 5,
            "min_score": 0.5
        },
        name="Search Endpoint"
    )

    # Test document listing
    test_endpoint("GET", "/documents/", name="List Documents")

    # Test vector stats
    test_endpoint("GET", "/search/stats", name="Vector Store Statistics")

    print(f"\n{'='*50}")
    print("✨ API testing complete!")
    print("\nNext steps:")
    print("1. Upload a document using POST /api/v1/documents/upload")
    print("2. Try searching with your queries")
    print("3. Test the chat functionality")
    print("\nAPI docs available at: http://localhost:8000/docs")


if __name__ == "__main__":
    main()