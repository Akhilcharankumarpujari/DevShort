import subprocess
import os

services = [
    "api-gateway",
    "user-service",
    "movie-service",
    "booking-service",
    "payment-service",
    "notification-service"
]

# Path to python.exe inside our virtual environment
current_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(current_dir, "venv", "Scripts", "python.exe")

results = {}

for service in services:
    print(f"\n==========================================")
    print(f"Running tests for: {service}")
    print(f"==========================================\n")
    
    cwd = os.path.join(current_dir, service)
    try:
        res = subprocess.run([venv_python, "-m", "pytest"], cwd=cwd, capture_output=True, text=True)
        if res.returncode == 0:
            results[service] = "PASSED"
            print(f"Result: {service} PASSED successfully!")
        else:
            results[service] = "FAILED"
            print(f"Result: {service} FAILED!")
            print(res.stdout)
            print(res.stderr)
    except Exception as e:
        results[service] = f"ERROR: {str(e)}"
        print(f"Error running tests for {service}: {str(e)}")

print("\n==========================================")
print("TEST SUMMARY RESULTS:")
print("==========================================")
for service, status in results.items():
    print(f"{service:<25}: {status}")
