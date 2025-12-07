"""
Simple latency tracking for performance monitoring
"""

import time

class LatencyTracker:
    def __init__(self):
        self.checkpoints = {}
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start timing"""
        self.start_time = time.time()
        self.checkpoints = {}
    
    def checkpoint(self, name: str):
        """Record a checkpoint"""
        self.checkpoints[name] = time.time()
    
    def stop(self):
        """Stop timing"""
        self.end_time = time.time()
    
    def get_report(self) -> dict:
        """
        Generate latency report
        Returns dict with component timings
        """
        if not self.start_time or not self.end_time:
            return {"error": "Timer not properly started/stopped"}
        
        report = {"total": self.end_time - self.start_time}
        
        # Calculate component latencies
        checkpoint_keys = sorted(self.checkpoints.keys())
        
        for i in range(0, len(checkpoint_keys), 2):
            if i + 1 < len(checkpoint_keys):
                start_key = checkpoint_keys[i]
                end_key = checkpoint_keys[i + 1]
                
                if start_key.endswith("_start") and end_key.endswith("_end"):
                    component_name = start_key.replace("_start", "")
                    duration = self.checkpoints[end_key] - self.checkpoints[start_key]
                    report[component_name] = duration
        
        return report