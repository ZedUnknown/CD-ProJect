import requests
import os
import time

os.system('cls')

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer <JUPYTER_TOKEN>" # replace with your actual token
}

kernel_url = "http://localhost:8888/api/kernels"

while True:
    os.system('cls')
    kernels_response = requests.get(kernel_url, headers=headers)
    kernels = kernels_response.json()

    kernel_id = None
    if kernels_response.status_code == 200:
        print("kernels_response.status_code == 200")
        print(f"kernels: {len(kernels)}")
        
        for kernel in kernels:
            print(f"kernel: {kernel}")

    else:
        print(f"Failed to get kernels: {kernels_response.text}")
        raise Exception("Failed to get kernels")

    time.sleep(2)