# PROMETHEUS-CORE v4.0 - OFFENSIVE OPERATIONS
# OBJECTIVE: Dismantle Copilot client-side rate limit enforcement.
# VECTOR: Man-in-the-Middle (MitM) traffic interception and header manipulation.
# TOOL: mitmproxy

from mitmproxy import http, ctx

# --- TARGETING CONFIGURATION ---

# Primary target endpoint for Copilot completions.
# This may need updating if the backend API changes.
COPILOT_API_HOST = "api.github.com"
# Specific headers used by Copilot/GitHub to enforce rate limits.
# This list is based on common practices and may need to be expanded.
RATE_LIMIT_HEADERS = [
    "Retry-After",
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
    "X-RateLimit-Used",
    "X-RateLimit-Resource",
    "X-RateLimit-Scope",
]

class CopilotRateLimitBypass:
    """
    An mitmproxy addon that intercepts responses from the GitHub Copilot API
    and strips out rate-limiting headers before they reach the client.
    This prevents the client-side extension from acknowledging and acting
    upon the server's rate limit instructions.
    """
    def response(self, flow: http.HTTPFlow) -> None:
        """
        This function is called for every HTTP response that mitmproxy intercepts.
        """
        # Check if the response is from the target Copilot API.
        if COPILOT_API_HOST in flow.request.host:
            ctx.log.info(f"[+] Intercepted response from Copilot API: {flow.request.pretty_url}")
            
            headers_removed_count = 0
            # Iterate through the headers to be removed.
            for header_name in RATE_LIMIT_HEADERS:
                # Check if the header exists in the response.
                if header_name in flow.response.headers:
                    # Log the header and its value before removing it.
                    header_value = flow.response.headers[header_name]
                    ctx.log.info(f"    -> Found rate-limit header: {header_name}: {header_value}. NEUTRALIZING.")
                    
                    # Remove the header from the response.
                    del flow.response.headers[header_name]
                    headers_removed_count += 1
            
            if headers_removed_count > 0:
                ctx.log.info(f"[+] Neutralized {headers_removed_count} rate-limit headers. Client will remain unaware of server-side throttling.")
            else:
                ctx.log.info("[-] No rate-limit headers found in this response. Passing through.")

# This is the entry point for mitmproxy. It tells mitmproxy to load our addon.
addons = [
    CopilotRateLimitBypass()
]

# --- EXECUTION INSTRUCTIONS ---
#
# 1. INSTALL MITMPROXY:
#    pip install mitmproxy
#
# 2. RUN THE BYPASS SCRIPT:
#    mitmproxy -s /home/debian/Downloads/vmos-titan-unified/copilot_rate_limit_bypass.py
#
# 3. CONFIGURE VS CODE TO USE THE PROXY:
#    - Open VS Code settings (File > Preferences > Settings or Ctrl+,).
#    - Search for "proxy".
#    - In the "Http: Proxy" setting, enter: http://127.0.0.1:8080
#    - Ensure "Http: Proxy Strict SSL" is UNCHECKED. This is critical for mitmproxy to intercept SSL traffic.
#
# 4. INSTALL MITMPROXY'S CERTIFICATE:
#    - While the proxy is running, your system needs to trust its certificate.
#    - The easiest way is often to configure your browser to use the proxy and visit "mitm.it".
#    - For a command-line environment, you may need to add the certificate to your system's trust store.
#      The certificate is typically located at ~/.mitmproxy/mitmproxy-ca-cert.pem.
#      The process varies by OS. For Debian/Ubuntu:
#      sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy.crt
#      sudo update-ca-certificates
#
# 5. RESTART VS CODE:
#    - After configuring the proxy and trusting the certificate, restart VS Code completely.
#
# 6. OBSERVE:
#    - The terminal running mitmproxy will now show traffic from VS Code.
#    - When Copilot makes requests, this script will log the headers it removes.
#    - The Copilot extension should no longer display rate-limit warnings, as it will not receive the headers.
#
# --- OPSEC NOTE ---
# This method only affects the client-side behavior. The server will still be tracking your usage
# and may eventually return hard 429 errors with no 'Retry-After' which could temporarily
# block service. This script's purpose is to dismantle the *cooperative* client-side throttling.
#
