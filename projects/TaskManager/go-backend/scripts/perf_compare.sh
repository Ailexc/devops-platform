#!/bin/bash
# perf_compare.sh — Performance comparison: Python vs Go backend.
# Runs the same task set and compares timing/memory.
# Usage: ./scripts/perf_compare.sh [PYTHON_URL] [GO_URL]

set -e

PYTHON_URL="${1:-http://localhost:8000}"
GO_URL="${2:-http://localhost:8080}"
TASKS=10
OUTPUT_DIR="./perf_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$OUTPUT_DIR"

echo "=== Performance Comparison: Python vs Go ==="
echo "Python: $PYTHON_URL"
echo "Go:     $GO_URL"
echo "Tasks:  $TASKS"
echo ""

# Test function
run_benchmark() {
    local name="$1"
    local url="$2"
    local output_file="$OUTPUT_DIR/${name}_${TIMESTAMP}.txt"
    
    echo "--- Benchmarking: $name ---"
    echo "URL: $url" > "$output_file"
    echo "Timestamp: $TIMESTAMP" >> "$output_file"
    echo "" >> "$output_file"
    
    # Memory usage before
    echo "=== Timing ===" >> "$output_file"
    
    total_time=0
    for i in $(seq 1 $TASKS); do
        start=$(date +%s%N)
        curl -s -o /dev/null "$url/api/v1/dashboard/stats/" 2>/dev/null
        end=$(date +%s%N)
        elapsed=$(( (end - start) / 1000000 ))
        total_time=$((total_time + elapsed))
        echo "Request $i: ${elapsed}ms" >> "$output_file"
    done
    
    avg_time=$((total_time / TASKS))
    echo "" >> "$output_file"
    echo "Total: ${total_time}ms" >> "$output_file"
    echo "Average: ${avg_time}ms" >> "$output_file"
    
    echo "  $name avg: ${avg_time}ms"
    echo ""
}

# Run benchmarks
run_benchmark "python" "$PYTHON_URL"
run_benchmark "go" "$GO_URL"

# Summary
echo "=== Summary ==="
echo "Results saved to: $OUTPUT_DIR/"
echo ""

# Compare with wrk if available
if command -v wrk &> /dev/null; then
    echo "--- wrk load test (10s, 4 threads) ---"
    echo "Python:" && wrk -t4 -c10 -d10s "$PYTHON_URL/api/v1/dashboard/stats/" 2>&1 | tail -3
    echo ""
    echo "Go:" && wrk -t4 -c10 -d10s "$GO_URL/api/v1/dashboard/stats/" 2>&1 | tail -3
else
    echo "Install 'wrk' for load testing: brew install wrk"
fi
