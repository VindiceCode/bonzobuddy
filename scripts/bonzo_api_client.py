"""
Bonzo API Client for superuser authentication and prospect validation.
"""

import http.client
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlencode, urlparse
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProspectData:
    """Prospect data from Bonzo API."""
    id: int
    business_entity_id: int
    first_name: str
    last_name: str
    full_name: str
    source: str
    email: Optional[str]
    phone: Optional[str]
    assigned_to: int
    assigned_user: Dict[str, Any]
    created_at: str
    updated_at: str
    business: Dict[str, Any]


class BonzoAPIError(Exception):
    """Bonzo API related errors."""
    pass


class BonzoAPIClient:
    """Client for interacting with Bonzo API using superuser authentication."""
    
    def __init__(self, superuser_api_key: str, base_url: str = "app.getbonzo.com"):
        """
        Initialize Bonzo API client.
        
        Args:
            superuser_api_key: Superuser API key for authentication
            base_url: Base URL for Bonzo API (default: app.getbonzo.com)
        """
        self.superuser_api_key = superuser_api_key
        self.base_url = base_url
        self.timeout = 30
        
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        user_id: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Bonzo API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            user_id: User ID for On-Behalf-Of header
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            BonzoAPIError: On API errors
        """
        try:
            conn = http.client.HTTPSConnection(self.base_url)
            
            # Prepare headers
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.superuser_api_key}',
                'Content-Type': 'application/json'
            }
            
            if user_id:
                headers['On-Behalf-Of'] = str(user_id)
            
            # Prepare URL with query parameters
            url = endpoint
            if params:
                url += '?' + urlencode(params)
            
            # Prepare request body
            request_data = None
            if data:
                request_data = json.dumps(data)
            
            logger.info(f"Making {method} request to {url}")
            if user_id:
                logger.info(f"Using On-Behalf-Of: {user_id}")
            
            # Make request
            conn.request(method, url, body=request_data, headers=headers)
            response = conn.getresponse()
            response_data = response.read()
            
            logger.info(f"Response status: {response.status}")
            
            # Parse response
            if response_data:
                try:
                    parsed_data = json.loads(response_data.decode('utf-8'))
                except json.JSONDecodeError:
                    parsed_data = {"raw_response": response_data.decode('utf-8')}
            else:
                parsed_data = {}
            
            # Check for errors
            if response.status >= 400:
                error_msg = f"API request failed with status {response.status}"
                if 'message' in parsed_data:
                    error_msg += f": {parsed_data['message']}"
                elif 'error' in parsed_data:
                    error_msg += f": {parsed_data['error']}"
                raise BonzoAPIError(error_msg)
            
            return parsed_data
            
        except Exception as e:
            if isinstance(e, BonzoAPIError):
                raise
            logger.error(f"API request failed: {e}")
            raise BonzoAPIError(f"API request failed: {e}")
        finally:
            conn.close()
    
    def get_user_prospects(
        self, 
        user_id: int, 
        limit: int = 100,
        created_after: Optional[str] = None
    ) -> List[ProspectData]:
        """
        Get prospects for a specific user using On-Behalf-Of.
        
        Args:
            user_id: User ID to get prospects for
            limit: Maximum number of prospects to return
            created_after: ISO datetime string to filter prospects created after
            
        Returns:
            List of ProspectData objects
        """
        params = {'limit': limit}
        if created_after:
            params['created_after'] = created_after
        
        logger.info(f"Getting prospects for user {user_id}")
        
        response = self._make_request(
            'GET', 
            '/api/v3/prospects',
            user_id=user_id,
            params=params
        )
        
        prospects = []
        for prospect_data in response.get('data', []):
            try:
                prospect = ProspectData(
                    id=prospect_data['id'],
                    business_entity_id=prospect_data['business_entity_id'],
                    first_name=prospect_data['first_name'],
                    last_name=prospect_data['last_name'],
                    full_name=prospect_data['full_name'],
                    source=prospect_data['source'],
                    email=prospect_data.get('email'),
                    phone=prospect_data.get('phone'),
                    assigned_to=prospect_data['assigned_to'],
                    assigned_user=prospect_data['assigned_user'],
                    created_at=prospect_data['created_at'],
                    updated_at=prospect_data['updated_at'],
                    business=prospect_data['business']
                )
                prospects.append(prospect)
            except KeyError as e:
                logger.warning(f"Skipping prospect due to missing field {e}: {prospect_data}")
                continue
        
        logger.info(f"Retrieved {len(prospects)} prospects for user {user_id}")
        return prospects
    
    def find_test_prospects(
        self,
        user_id: int,
        test_pattern: str,
        created_after: Optional[str] = None
    ) -> List[ProspectData]:
        """
        Find test prospects by name pattern for a specific user.
        
        Args:
            user_id: User ID to search prospects for
            test_pattern: Pattern to match in prospect names (e.g., "TestRecord_MonitorBase")
            created_after: ISO datetime string to filter prospects created after
            
        Returns:
            List of matching ProspectData objects
        """
        all_prospects = self.get_user_prospects(user_id, created_after=created_after)
        
        test_prospects = []
        for prospect in all_prospects:
            if (test_pattern.lower() in prospect.first_name.lower() or 
                test_pattern.lower() in prospect.last_name.lower() or
                test_pattern.lower() in prospect.full_name.lower()):
                test_prospects.append(prospect)
        
        logger.info(f"Found {len(test_prospects)} test prospects matching '{test_pattern}' for user {user_id}")
        return test_prospects
    
    def validate_prospect_assignment(
        self,
        prospect: ProspectData,
        expected_user_email: str,
        expected_user_id: int,
        expected_team_id: int
    ) -> Dict[str, bool]:
        """
        Validate that a prospect is assigned correctly.
        
        Args:
            prospect: ProspectData to validate
            expected_user_email: Expected assigned user email
            expected_user_id: Expected assigned user ID
            expected_team_id: Expected team ID
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'user_email_match': False,
            'user_id_match': False,
            'team_id_match': False,
            'assigned_to_match': False
        }
        
        # Check assigned user email
        if prospect.assigned_user.get('email') == expected_user_email:
            results['user_email_match'] = True
        
        # Check assigned user ID
        if prospect.assigned_user.get('id') == expected_user_id:
            results['user_id_match'] = True
        
        # Check team ID (business entity ID)
        if prospect.business_entity_id == expected_team_id:
            results['team_id_match'] = True
        
        # Check assigned_to field
        if prospect.assigned_to == expected_user_id:
            results['assigned_to_match'] = True
        
        return results
    
    def wait_for_prospects(
        self,
        user_id: int,
        test_pattern: str,
        expected_count: int,
        timeout: int = 300,
        check_interval: int = 10
    ) -> List[ProspectData]:
        """
        Wait for test prospects to appear in Bonzo with polling.
        
        Args:
            user_id: User ID to check
            test_pattern: Pattern to match in prospect names
            expected_count: Expected number of test prospects
            timeout: Maximum time to wait in seconds
            check_interval: Time between checks in seconds
            
        Returns:
            List of found ProspectData objects
            
        Raises:
            TimeoutError: If expected prospects don't appear within timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            prospects = self.find_test_prospects(user_id, test_pattern)
            
            logger.info(f"Found {len(prospects)}/{expected_count} test prospects for user {user_id}")
            
            if len(prospects) >= expected_count:
                return prospects
            
            time.sleep(check_interval)
        
        raise TimeoutError(
            f"Timed out waiting for {expected_count} test prospects for user {user_id}. "
            f"Found {len(prospects)} after {timeout} seconds."
        )