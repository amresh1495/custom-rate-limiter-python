from flask import Flask, request, jsonify
from rate_limiter import RateLimiter

app = Flask(__name__)

# Initialize RateLimiter
# Default: 5 requests per 15 seconds for any endpoint not specifically configured
rate_limiter = RateLimiter(default_requests_limit=5, default_window_size_seconds=15)

# Specific rules for endpoints
# '/limited' endpoint: 2 requests per 10 seconds
rate_limiter.add_endpoint_rule(endpoint='/limited', requests_limit=2, window_size_seconds=10)
# '/unlimited' endpoint: A very high limit to simulate no effective rate limiting
rate_limiter.add_endpoint_rule(endpoint='/unlimited', requests_limit=1000, window_size_seconds=60) # Effectively unlimited for typical use

# Helper function to get client IP address
def get_client_ip():
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    return request.remote_addr

@app.route('/')
def home():
    client_ip = get_client_ip()
    # Check if request is allowed using the 'default' endpoint configuration in RateLimiter
    if rate_limiter.is_allowed(client_id=client_ip, endpoint='/'): # Using '/' as endpoint identifier
        return jsonify(message="Welcome to the homepage! (Default Rate Limit)"), 200
    else:
        return jsonify(error="Rate limit exceeded for default endpoint. Please try again later."), 429

@app.route('/limited')
def limited_endpoint():
    client_ip = get_client_ip()
    # Check if request is allowed using the specific '/limited' endpoint configuration
    if rate_limiter.is_allowed(client_id=client_ip, endpoint='/limited'):
        return jsonify(message="This is a limited endpoint. (2 requests per 10 seconds)"), 200
    else:
        return jsonify(error="Rate limit exceeded for /limited endpoint. Please try again later."), 429

@app.route('/unlimited')
def unlimited_endpoint():
    client_ip = get_client_ip()
    # This endpoint has a very high limit, effectively making it unlimited for normal use
    # We still pass it through the rate limiter to demonstrate the mechanism
    if rate_limiter.is_allowed(client_id=client_ip, endpoint='/unlimited'):
        return jsonify(message="This endpoint is effectively unlimited."), 200
    else:
        # This case should ideally not be hit with the high limit set
        return jsonify(error="Rate limit exceeded for /unlimited endpoint (should not happen)."), 429

if __name__ == '__main__':
    print("Starting Flask app on http://127.0.0.1:5000")
    print("Endpoints:")
    print("  GET /          (Default Limit: 5 requests / 15 seconds per IP)")
    print("  GET /limited   (Specific Limit: 2 requests / 10 seconds per IP)")
    print("  GET /unlimited (Effectively Unlimited: 1000 requests / 60 seconds per IP)")
    app.run(debug=True, port=5000)
