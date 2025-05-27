# Custom Rate Limiter

## Project Overview

This project implements a Flask web application with a custom rate limiting mechanism. The core of the project is the `RateLimiter` class, which uses a rolling sliding window algorithm to control the number of requests clients can make to different API endpoints. The application demonstrates default rate limits, endpoint-specific rate limits, and effectively unlimited access for certain endpoints.

## Project Structure

The project is organized as follows:

```
.
├── app/
│   ├── __init__.py         # Makes 'app' a Python package (optional, but good practice)
│   ├── main.py             # Contains the Flask application logic and endpoint definitions.
│   └── rate_limiter.py     # Contains the RateLimiter class implementation.
├── requirements.txt        # Lists project dependencies (e.g., Flask).
└── README.md               # This file.
```

-   **`app/`**: This directory contains the core application code.
    -   **`app/main.py`**: This file sets up the Flask server and defines the API endpoints (`/`, `/limited`, `/unlimited`). It integrates the `RateLimiter` to protect these endpoints.
    -   **`app/rate_limiter.py`**: This module provides the `RateLimiter` class, which is responsible for tracking request counts and enforcing limits.
-   **`requirements.txt`**: This file specifies the Python packages required to run the project.
-   **`README.md`**: Provides documentation for the project.

## Architecture

### `RateLimiter` Class

The `RateLimiter` class is the heart of the rate limiting system.
-   **Initialization**: When instantiated, it can be configured with `default_requests_limit` and `default_window_size_seconds` that apply to any client request not covered by a specific endpoint rule.
-   **Endpoint Rules**: Specific rules can be added using the `add_endpoint_rule(endpoint, requests_limit, window_size_seconds)` method. This allows different endpoints to have different rate limits.
-   **Request Tracking**: It stores request timestamps in a dictionary where keys are `client_id` and then `endpoint`. The values are lists of timestamps.
    - `self.client_requests[client_id][endpoint] = [timestamp1, timestamp2, ...]`
-   **Checking Allowance**: The `is_allowed(client_id, endpoint)` method determines if a request should be permitted. It retrieves the relevant timestamps for the client and endpoint, removes outdated ones (older than the window size), and then checks if the count of recent requests is below the configured limit.

### Flask Application Integration

The `RateLimiter` is integrated into the Flask application (`app/main.py`) as follows:
1.  An instance of `RateLimiter` is created globally when the Flask app starts.
2.  Default limits and specific endpoint rules (for `/limited` and `/unlimited`) are configured on this instance.
3.  For each incoming request to a rate-limited endpoint:
    -   The client's IP address is retrieved using a helper function `get_client_ip()`.
    -   The `rate_limiter.is_allowed(client_ip, endpoint_name)` method is called.
    -   If `is_allowed` returns `True`, the request is processed, and the endpoint's logic is executed.
    -   If `is_allowed` returns `False`, the application returns an HTTP 429 (Too Many Requests) error.

### Client Identification

Clients are identified by their IP address. The `get_client_ip()` function in `app/main.py` attempts to get the IP address, considering common proxy headers like `X-Forwarded-For`. This IP address is then used as the `client_id` for the `RateLimiter`.

## Algorithm

### Rolling Sliding Window Algorithm

The `RateLimiter` employs a **Rolling Sliding Window** (also known as Sliding Window Log) algorithm. Here’s how it works:

1.  **Timestamp Logging**: For each allowed request from a specific client to a specific endpoint, the current timestamp is recorded and stored in a list associated with that client/endpoint pair.
2.  **Window Definition**: A time window is defined by its size (e.g., 60 seconds). This window is "rolling" or "sliding" because its start time is always `current_time - window_size`.
3.  **Request Check**: When a new request arrives:
    a.  All timestamps in the client/endpoint's list that are older than the start of the current window (i.e., `timestamp <= current_time - window_size`) are discarded. This is the "sliding" action, as old requests effectively expire and are removed from consideration.
    b.  The number of remaining timestamps (those within the current window) is counted.
    c.  If this count is less than the `requests_limit` for that endpoint (or the default limit if no specific rule applies), the new request is allowed, and its timestamp is added to the list.
    d.  If the count is equal to or greater than the `requests_limit`, the request is denied.

This approach is more accurate than fixed window algorithms as it doesn't suffer from edge effects where a burst of requests at the boundary of two fixed windows could exceed the intended rate.

## Features

-   **Multiple Client Support**: The rate limiter tracks requests independently for each client (identified by IP address). One client exceeding its limit does not affect others.
-   **Endpoint-Specific Rule Overriding**: Different endpoints can have distinct rate limits. For example, `/api/search` might allow more requests per minute than `/api/submit_form`. This is configured via `rate_limiter.add_endpoint_rule()`.
-   **Default Rate Limiting**: A global default rate limit applies to any endpoint that doesn't have a specific rule.
-   **Rolling Sliding Window**: Provides accurate rate limiting by maintaining a log of request timestamps.

## Setup and Usage

### 1. Prerequisites

-   Python 3.7+
-   `pip` (Python package installer)

### 2. Installation

Clone the repository.

Navigate to the project's root directory (where `requirements.txt` is located) and install the necessary dependencies:

```bash
pip install -r requirements.txt
```

This will install Flask and any other required packages.

### 3. Running the Flask Application

To run the Flask application, execute the `main.py` script from within the `app` directory or its parent:

```bash
python app/main.py
```

Or, if you are in the root directory:

```bash
python -m app.main
```

The application will start, typically on `http://127.0.0.1:5000`. You should see output similar to:

```
Starting Flask app on http://127.0.0.1:5000
Endpoints:
  GET /          (Default Limit: 5 requests / 15 seconds per IP)
  GET /limited   (Specific Limit: 2 requests / 10 seconds per IP)
  GET /unlimited (Effectively Unlimited: 1000 requests / 60 seconds per IP)
 * Serving Flask app 'main'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://<your-local-ip>:5000
Press CTRL+C to quit
```

### 4. Testing with `curl`

You can test the rate limiter using `curl` or any API client (like Postman, or even your web browser for GET requests).

**Assumptions for `curl` examples:**
- The server is running on `127.0.0.1:5000`.
- Your IP address will be used as the client identifier.

**a) Testing the Default Endpoint (`/`)**
Default limit: 5 requests per 15 seconds.

Open your terminal and run the following command multiple times:

```bash
curl -i http://127.0.0.1:5000/
```

-   The first 5 requests (within a 15-second window) should return an HTTP 200 status and a JSON message.
-   The 6th request (and subsequent ones within the window) should return an HTTP 429 (Too Many Requests) error.
-   Wait for 15 seconds for the window to slide, then try again; you should be allowed.

Example of an allowed response:
```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 68
Server: Werkzeug/2.0.3 Python/3.x.x
Date: <current_date_time>

{
  "message": "Welcome to the homepage! (Default Rate Limit)"
}
```

Example of a denied response (after exceeding the limit):
```http
HTTP/1.1 429 TOO MANY REQUESTS
Content-Type: application/json
Content-Length: 85
Server: Werkzeug/2.0.3 Python/3.x.x
Date: <current_date_time>

{
  "error": "Rate limit exceeded for default endpoint. Please try again later."
}
```

**b) Testing the Limited Endpoint (`/limited`)**
Specific limit: 2 requests per 10 seconds.

```bash
curl -i http://127.0.0.1:5000/limited
```
-   The first 2 requests (within a 10-second window) should be allowed (HTTP 200).
-   The 3rd request should be denied (HTTP 429).
-   Wait for 10 seconds, then try again.

**c) Testing the Unlimited Endpoint (`/unlimited`)**
Effectively unlimited (configured with a very high limit: 1000 requests per 60 seconds).

```bash
curl -i http://127.0.0.1:5000/unlimited
```
-   You should be able to make many requests to this endpoint without being rate-limited. It will return an HTTP 200 status.