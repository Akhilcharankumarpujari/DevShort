import subprocess
import os

services = [
    ("api-gateway", "cineops-api-gateway"),
    ("user-service", "cineops-user-service"),
    ("movie-service", "cineops-movie-service"),
    ("booking-service", "cineops-booking-service"),
    ("payment-service", "cineops-payment-service"),
    ("notification-service", "cineops-notification-service")
]

current_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Get Minikube's Docker daemon environment variables
print("Retrieving Minikube's Docker daemon environment...")
env = os.environ.copy()
env_res = subprocess.run(["minikube", "docker-env", "--shell", "cmd"], capture_output=True, text=True, encoding="utf-8", errors="replace")
if env_res.returncode == 0:
    for line in env_res.stdout.splitlines():
        if line.startswith("SET "):
            parts = line[4:].split("=", 1)
            if len(parts) == 2:
                key, val = parts
                env[key.strip()] = val.strip()
                print(f"Set env: {key.strip()} = {val.strip()}")
else:
    print("Warning: Could not get Minikube docker-env.")

# 2. Build each service directly in Minikube's docker daemon
for service_dir, image_name in services:
    tag = f"{image_name}:latest"
    print(f"\n==========================================")
    print(f"Building Docker image for: {service_dir} -> {tag}")
    print(f"==========================================\n")
    
    cwd = os.path.join(current_dir, service_dir)
    # Stream stdout/stderr directly to terminal to prevent encoding crashes or buffering bottlenecks
    build_res = subprocess.run(["docker", "build", "-t", tag, "."], cwd=cwd, env=env)
    if build_res.returncode != 0:
        print(f"Build failed for {service_dir}!")
        exit(1)
    print(f"Successfully built {tag} directly in Minikube's Docker daemon!")

print("\n==========================================")
print("All images built directly in Minikube successfully!")
print("==========================================")
