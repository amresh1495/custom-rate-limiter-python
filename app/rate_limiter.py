import time
from collections import defaultdict

class RateLimiter:
    """
    A rate limiter implementation using the rolling sliding window algorithm.
    It supports multiple clients and endpoint-specific rate limiting rules.
    """

    def __init__(self, default_requests_limit: int, default_window_size_seconds: int):
        """
        Initializes the RateLimiter.
        """
        if not isinstance(default_requests_limit, int) or default_requests_limit <= 0:
            raise ValueError("Default requests limit must be a positive integer.")
        if not isinstance(default_window_size_seconds, int) or default_window_size_seconds <= 0:
            raise ValueError("Default window size must be a positive integer.")

        self.default_requests_limit = default_requests_limit
        self.default_window_size_seconds = default_window_size_seconds
        # Stores request timestamps for each client and endpoint combination.
        # Structure: self.client_requests[client_id][endpoint] = [timestamp1, timestamp2, ...]
        self.client_requests = defaultdict(lambda: defaultdict(list))
        # Stores endpoint-specific rules.
        # Structure: self.endpoint_rules[endpoint] = (requests_limit, window_size_seconds)
        self.endpoint_rules = {}

    def add_endpoint_rule(self, endpoint: str, requests_limit: int, window_size_seconds: int):
        """
        Adds or updates an endpoint-specific rate limiting rule.
        """
        if not isinstance(endpoint, str) or not endpoint:
            raise ValueError("Endpoint must be a non-empty string.")
        if not isinstance(requests_limit, int) or requests_limit <= 0:
            raise ValueError("Requests limit must be a positive integer.")
        if not isinstance(window_size_seconds, int) or window_size_seconds <= 0:
            raise ValueError("Window size must be a positive integer.")

        self.endpoint_rules[endpoint] = (requests_limit, window_size_seconds)
        # print(f"Rule added for endpoint '{endpoint}': {requests_limit} requests per {window_size_seconds}s")

    def is_allowed(self, client_id: str, endpoint: str = "default") -> bool:
        """
        Checks if a request from a given client for a specific endpoint is allowed.

        The method employs a rolling window algorithm. For each incoming request, it first
        determines the applicable rate limit (endpoint-specific or default). It then
        retrieves the timestamps of previous requests from the same client for the same
        endpoint. Timestamps older than the defined window size (from the current time)
        are discarded. This "slides" the window. If the count of remaining timestamps
        (i.e., requests within the current window) is less than the allowed limit,
        the current request is permitted, and its timestamp is recorded. Otherwise,
        the request is denied.
        """
        if not isinstance(client_id, str) or not client_id:
            raise ValueError("Client ID must be a non-empty string.")
        # Allow "default" as a valid endpoint string, but not an empty string if user provides it.
        if not isinstance(endpoint, str) or not endpoint:
             raise ValueError("Endpoint must be a non-empty string.")


        current_time = time.time()

        # Determine the applicable rate limit and window size
        # If an endpoint-specific rule exists, use it; otherwise, use default settings.
        if endpoint != "default" and endpoint in self.endpoint_rules: # Check if specific rule exists
            requests_limit, window_size = self.endpoint_rules[endpoint]
        else: # Fallback to default rules
            requests_limit, window_size = self.default_requests_limit, self.default_window_size_seconds

        # Get the list of request timestamps for the current client and endpoint.
        # If it's the first request from this client for this endpoint, an empty list is implicitly created.
        request_timestamps = self.client_requests[client_id][endpoint]

        # Remove timestamps that are older than the current window (current_time - window_size).
        # This ensures that only requests within the rolling window are considered.
        # This is the "sliding" part of the window.
        relevant_timestamps = [ts for ts in request_timestamps if ts > current_time - window_size]
        self.client_requests[client_id][endpoint] = relevant_timestamps

        # Check if the number of requests in the current window is less than the allowed limit.
        if len(relevant_timestamps) < requests_limit:
            # If allowed, add the current request's timestamp to the list.
            self.client_requests[client_id][endpoint].append(current_time)
            return True
        else:
            # If the limit is reached or exceeded, the request is denied.
            print(f"Rate limit exceeded for client '{client_id}' at endpoint '{endpoint}'. "
                  f"Limit: {requests_limit} req/{window_size}s. "
                  f"Requests in window: {len(relevant_timestamps)}")
            return False
