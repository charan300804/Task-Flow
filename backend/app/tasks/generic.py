import time
import math
import numpy as np
from typing import Dict, Any

def execute_sleep_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    duration = payload.get("duration_seconds", 3)
    time.sleep(duration)
    return {"message": f"Slept successfully for {duration} seconds", "duration": duration}

def execute_cpu_prime_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    limit = payload.get("limit", 20000)
    start_time = time.time()
    
    primes = []
    for num in range(2, limit + 1):
        is_prime = True
        for i in range(2, int(math.isqrt(num)) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(num)
            
    execution_time_ms = int((time.time() - start_time) * 1000)
    return {
        "limit": limit,
        "prime_count": len(primes),
        "largest_prime": primes[-1] if primes else None,
        "execution_time_ms": execution_time_ms
    }

def execute_matrix_computation_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    matrix_size = payload.get("size", 300)
    start_time = time.time()
    
    A = np.random.rand(matrix_size, matrix_size)
    B = np.random.rand(matrix_size, matrix_size)
    C = np.dot(A, B)
    
    execution_time_ms = int((time.time() - start_time) * 1000)
    return {
        "matrix_size": f"{matrix_size}x{matrix_size}",
        "trace": float(np.trace(C)),
        "mean": float(np.mean(C)),
        "execution_time_ms": execution_time_ms
    }

def execute_data_processing_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    items_count = payload.get("items_count", 5000)
    start_time = time.time()
    
    data = [{"id": i, "val": i * 1.5, "group": f"group_{i % 5}"} for i in range(items_count)]
    groups = {}
    for item in data:
        g = item["group"]
        if g not in groups:
            groups[g] = []
        groups[g].append(item["val"])
        
    group_stats = {g: {"count": len(vals), "avg": sum(vals)/len(vals)} for g, vals in groups.items()}
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    return {
        "items_processed": items_count,
        "group_stats": group_stats,
        "execution_time_ms": execution_time_ms
    }
