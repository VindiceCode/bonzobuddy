"""
Webhook delivery testing utilities for bulk integration testing.
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import concurrent.futures
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class WebhookResponse:
    """Webhook response data."""
    record_id: str
    status_code: int
    response_text: str
    response_time: float
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class WebhookDeliveryStats:
    """Statistics for webhook delivery testing."""
    total_sent: int
    successful: int
    failed: int
    avg_response_time: float
    max_response_time: float
    min_response_time: float
    success_rate: float
    responses: List[WebhookResponse]
    
    @classmethod
    def from_responses(cls, responses: List[WebhookResponse]) -> 'WebhookDeliveryStats':
        """Create stats from list of responses."""
        total_sent = len(responses)
        successful = sum(1 for r in responses if 200 <= r.status_code < 300)
        failed = total_sent - successful
        
        response_times = [r.response_time for r in responses if r.response_time > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        success_rate = (successful / total_sent * 100) if total_sent > 0 else 0
        
        return cls(
            total_sent=total_sent,
            successful=successful,
            failed=failed,
            avg_response_time=avg_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            success_rate=success_rate,
            responses=responses
        )


class WebhookValidator:
    """Validator for testing webhook delivery and responses."""
    
    def __init__(self, config, webhook_url: Optional[str] = None):
        """
        Initialize webhook validator.
        
        Args:
            config: Test configuration object
            webhook_url: Custom webhook URL to override config default
        """
        self.config = config
        self.webhook_url = webhook_url or config.webhook_url
        self.webhook_settings = getattr(config, 'webhook_settings', {})
        self.timeout = self.webhook_settings.get('timeout', 30)
        self.retry_attempts = self.webhook_settings.get('retry_attempts', 3)
        self.retry_delay = self.webhook_settings.get('retry_delay', 5)
        self.concurrent_requests = self.webhook_settings.get('concurrent_requests', 5)
    
    async def send_webhook_async(
        self, 
        record_id: str, 
        payload: Dict[str, Any],
        session: aiohttp.ClientSession
    ) -> WebhookResponse:
        """
        Send single webhook request asynchronously.
        
        Args:
            record_id: Unique record identifier
            payload: Payload to send
            session: aiohttp session
            
        Returns:
            WebhookResponse object
        """
        start_time = time.time()
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'BonzoBuddy-IntegrationTest/1.0'
            }
            
            logger.debug(f"Sending webhook for record {record_id}")
            
            async with session.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response_time = time.time() - start_time
                response_text = await response.text()
                
                webhook_response = WebhookResponse(
                    record_id=record_id,
                    status_code=response.status,
                    response_text=response_text[:1000],  # Limit response text
                    response_time=response_time
                )
                
                logger.info(f"Webhook {record_id}: {response.status} in {response_time:.2f}s")
                return webhook_response
                
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            error_msg = f"Timeout after {self.timeout}s"
            logger.warning(f"Webhook {record_id}: {error_msg}")
            
            return WebhookResponse(
                record_id=record_id,
                status_code=0,
                response_text="",
                response_time=response_time,
                error=error_msg
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"Request failed: {str(e)}"
            logger.error(f"Webhook {record_id}: {error_msg}")
            
            return WebhookResponse(
                record_id=record_id,
                status_code=0,
                response_text="",
                response_time=response_time,
                error=error_msg
            )
    
    async def send_bulk_webhooks_async(self, test_records: List) -> List[WebhookResponse]:
        """
        Send multiple webhook requests asynchronously with concurrency control.
        
        Args:
            test_records: List of test records to send
            
        Returns:
            List of WebhookResponse objects
        """
        connector = aiohttp.TCPConnector(limit=self.concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.concurrent_requests)
            
            async def send_with_semaphore(record):
                async with semaphore:
                    return await self.send_webhook_async(record.record_id, record.payload, session)
            
            # Execute all requests concurrently
            logger.info(f"Sending {len(test_records)} webhooks with {self.concurrent_requests} concurrent requests")
            tasks = [send_with_semaphore(record) for record in test_records]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions that occurred
            webhook_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.error(f"Exception in webhook {test_records[i].record_id}: {response}")
                    webhook_responses.append(WebhookResponse(
                        record_id=test_records[i].record_id,
                        status_code=0,
                        response_text="",
                        response_time=0,
                        error=str(response)
                    ))
                else:
                    webhook_responses.append(response)
            
            return webhook_responses
    
    def send_bulk_webhooks_sync(self, test_records: List) -> List[WebhookResponse]:
        """
        Send bulk webhooks synchronously (wrapper for async method).
        
        Args:
            test_records: List of test records to send
            
        Returns:
            List of WebhookResponse objects
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_bulk_webhooks_async(test_records))
    
    def send_webhook_with_retry(
        self, 
        record_id: str, 
        payload: Dict[str, Any]
    ) -> WebhookResponse:
        """
        Send webhook with retry logic (synchronous).
        
        Args:
            record_id: Unique record identifier
            payload: Payload to send
            
        Returns:
            WebhookResponse object
        """
        import requests
        
        last_response = None
        
        for attempt in range(self.retry_attempts):
            try:
                start_time = time.time()
                
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'BonzoBuddy-IntegrationTest/1.0'
                }
                
                logger.debug(f"Sending webhook for record {record_id} (attempt {attempt + 1})")
                
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                response_time = time.time() - start_time
                
                webhook_response = WebhookResponse(
                    record_id=record_id,
                    status_code=response.status_code,
                    response_text=response.text[:1000],
                    response_time=response_time
                )
                
                # If successful, return immediately
                if 200 <= response.status_code < 300:
                    logger.info(f"Webhook {record_id}: {response.status_code} in {response_time:.2f}s")
                    return webhook_response
                
                # If not successful, store response and potentially retry
                last_response = webhook_response
                logger.warning(f"Webhook {record_id}: {response.status_code} (attempt {attempt + 1})")
                
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                
            except requests.exceptions.Timeout:
                response_time = time.time() - start_time
                error_msg = f"Timeout after {self.timeout}s"
                last_response = WebhookResponse(
                    record_id=record_id,
                    status_code=0,
                    response_text="",
                    response_time=response_time,
                    error=error_msg
                )
                logger.warning(f"Webhook {record_id}: {error_msg} (attempt {attempt + 1})")
                
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                response_time = time.time() - start_time
                error_msg = f"Request failed: {str(e)}"
                last_response = WebhookResponse(
                    record_id=record_id,
                    status_code=0,
                    response_text="",
                    response_time=response_time,
                    error=error_msg
                )
                logger.error(f"Webhook {record_id}: {error_msg} (attempt {attempt + 1})")
                
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
        
        return last_response
    
    def validate_webhook_endpoint(self) -> Dict[str, Any]:
        """
        Validate webhook endpoint availability and configuration.
        
        Returns:
            Validation results dictionary
        """
        import requests
        
        results = {
            'endpoint_reachable': False,
            'supports_post': False,
            'accepts_json': False,
            'response_time': 0,
            'error': None
        }
        
        try:
            # Parse URL to check validity
            parsed_url = urlparse(self.config.webhook_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                results['error'] = "Invalid webhook URL format"
                return results
            
            # Test endpoint with minimal payload
            test_payload = {"test": "endpoint_validation"}
            start_time = time.time()
            
            response = requests.post(
                self.webhook_url,
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=self.timeout
            )
            
            results['response_time'] = time.time() - start_time
            results['endpoint_reachable'] = True
            results['supports_post'] = True
            results['accepts_json'] = True
            results['status_code'] = response.status_code
            results['response_text'] = response.text[:500]
            
            logger.info(f"Webhook endpoint validation: {response.status_code} in {results['response_time']:.2f}s")
            
        except requests.exceptions.Timeout:
            results['error'] = f"Endpoint timeout after {self.timeout}s"
            logger.warning(f"Webhook endpoint validation failed: {results['error']}")
            
        except requests.exceptions.ConnectionError:
            results['error'] = "Cannot connect to webhook endpoint"
            logger.warning(f"Webhook endpoint validation failed: {results['error']}")
            
        except Exception as e:
            results['error'] = f"Validation failed: {str(e)}"
            logger.error(f"Webhook endpoint validation failed: {results['error']}")
        
        return results
    
    def generate_delivery_report(
        self, 
        responses: List[WebhookResponse],
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed delivery report.
        
        Args:
            responses: List of webhook responses
            output_file: Optional output file path
            
        Returns:
            Report dictionary
        """
        stats = WebhookDeliveryStats.from_responses(responses)
        
        # Group responses by status code
        status_groups = {}
        for response in responses:
            status = response.status_code
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(response)
        
        # Identify failures
        failures = [r for r in responses if r.status_code < 200 or r.status_code >= 300]
        
        report = {
            'summary': {
                'total_requests': stats.total_sent,
                'successful_requests': stats.successful,
                'failed_requests': stats.failed,
                'success_rate_percent': round(stats.success_rate, 2),
                'avg_response_time_seconds': round(stats.avg_response_time, 3),
                'max_response_time_seconds': round(stats.max_response_time, 3),
                'min_response_time_seconds': round(stats.min_response_time, 3)
            },
            'status_code_breakdown': {
                str(status): len(responses) 
                for status, responses in status_groups.items()
            },
            'failures': [
                {
                    'record_id': r.record_id,
                    'status_code': r.status_code,
                    'error': r.error,
                    'response_text': r.response_text[:200] if r.response_text else None,
                    'response_time': round(r.response_time, 3)
                }
                for r in failures
            ],
            'performance_metrics': {
                'requests_per_second': round(stats.total_sent / max(stats.max_response_time, 1), 2),
                'fastest_response': round(stats.min_response_time, 3),
                'slowest_response': round(stats.max_response_time, 3)
            },
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Delivery report saved to {output_file}")
        
        return report