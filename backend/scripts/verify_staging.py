import argparse
import sys
import time
import httpx

def main():
    parser = argparse.ArgumentParser(description="Staging smoke test health verifier")
    parser.add_argument("--url", required=True, help="Base URL of the deployed staging API (e.g. https://staging-api.hireiq.com)")
    parser.add_argument("--retries", type=int, default=12, help="Number of times to retry health checks (useful for cold starts)")
    parser.add_argument("--delay", type=int, default=10, help="Delay in seconds between retries")
    args = parser.parse_args()

    # Clean URL string
    if not args.url or not args.url.strip() or not args.url.startswith("http"):
        print("=" * 60)
        print(" HIREIQ STAGING DEPLOYMENT SMOKE TEST ")
        print("=" * 60)
        print("[INFO] No valid staging URL provided (STAGING_API_URL secret is likely unconfigured).")
        print("Skipping smoke test verification.")
        print("=" * 60)
        sys.exit(0)

    base_url = args.url.strip().rstrip("/")
    health_url = f"{base_url}/health"

    print("=" * 60)
    print(" HIREIQ STAGING DEPLOYMENT SMOKE TEST ")
    print("=" * 60)
    print(f"Target Health URL: {health_url}")
    print(f"Max Retries: {args.retries} (with {args.delay}s delay)")
    print("=" * 60)

    for attempt in range(1, args.retries + 1):
        print(f"\n[Attempt {attempt}/{args.retries}] Sending health request...")
        try:
            # Send request with a 10s timeout
            response = httpx.get(health_url, timeout=10.0)
            status_code = response.status_code
            print(f"Response received. Status Code: {status_code}")

            if status_code == 200:
                data = response.json()
                status = data.get("status")
                database = data.get("database")
                redis = data.get("redis")
                print(f"Payload Status: '{status}'")
                print(f"Database Connectivity: '{database}'")
                print(f"Redis Connectivity: '{redis}'")

                if status == "healthy" and database == "connected":
                    print("\n" + "=" * 60)
                    print("[PASS] Deployed Staging environment is healthy and fully connected!")
                    print("=" * 60 + "\n")
                    sys.exit(0)
                else:
                    print(f"[WARN] API returned 200 but backend is unhealthy or database is not connected.")
            elif status_code == 503:
                try:
                    data = response.json()
                    print(f"[WARN] Service Unavailable (503). Database is likely unreachable.")
                    print(f"Details: {data.get('error')}")
                except Exception:
                    print(f"[WARN] Service Unavailable (503). No JSON payload.")
            else:
                print(f"[WARN] Non-success HTTP status code received: {status_code}")
                
        except httpx.RequestError as e:
            print(f"[WARN] HTTP request failed: {e}")
        except Exception as e:
            print(f"[WARN] Unexpected exception occurred: {e}")

        if attempt < args.retries:
            print(f"Waiting {args.delay} seconds before next attempt...")
            time.sleep(args.delay)

    print("\n" + "=" * 60)
    print("[FAIL] Staging environment failed smoke test verification after max retries.")
    print("=" * 60 + "\n")
    sys.exit(1)

if __name__ == "__main__":
    main()
