import httpx
import argparse
import sys

# EdgeCine Professional CLI Search Tool
# This tool demonstrates multi-environment versatility (Web + Terminal).
# Perfect for engineering-focused testing and demonstrations.

API_BASE_URL = "http://localhost:8000/films"

def run_search(query: str, limit: int = 5):
    """Executes a hybrid search via the EdgeCine backend API."""
    print(f"\n" + "="*60)
    print(f" EDGECINE HYBRID ENGINE | Query: '{query}'")
    print("="*60)

    try:
        # We use httpx for modern async-capable synchronous requests
        params = {"q": query, "limit": limit}
        response = httpx.get(f"{API_BASE_URL}/recommend", params=params, timeout=10.0)
        
        if response.status_code == 404:
            print("Error: Backend API not found. Is the server running?")
            return

        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        header_msg = data.get("neural_insight", "Discovery complete.")
        telemetry = data.get("telemetry", {})

        print(f"AI Insight: {header_msg}")
        print(f"Latency: {telemetry.get('inference_time_ms', 'N/A')}ms | Engine: {telemetry.get('vector_engine')}")
        print("-" * 60)

        if not results:
            print(" No results found for this query.")
        else:
            for i, res in enumerate(results, 1):
                match_pct = int(res['rank'] * 100)
                print(f"[{i}] {res['title']} ({res['year']})")
                print(f"    Match Score: {match_pct}% | {res.get('type', 'Unknown')}")
                print(f"    Reason: {res['match_reason']}")
                # Truncate description for terminal readability
                desc = res['description']
                print(f"    Description: {desc[:120]}..." if len(desc) > 120 else f"    Description: {desc}")
                print("-" * 60)

        print(f" Done. Displaying top {len(results)} of k=100 fused candidates.\n")

    except httpx.ConnectError:
        print(f"Error: Connection Error: Could not reach backend at {API_BASE_URL}.")
        print("   Make sure the FastAPI server is running (`npm run dev:backend` or Docker).")
    except Exception as e:
        print(f"Error: An error occurred: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EdgeCine Professional CLI Search Tool")
    parser.add_argument("query", type=str, help="The search query")
    parser.add_argument("--limit", type=int, default=5, help="Number of results to return (default: 5)")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    run_search(args.query, args.limit)
