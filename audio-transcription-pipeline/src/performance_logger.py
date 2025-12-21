#!/usr/bin/env python3
"""
Performance Logger for Audio Transcription Pipeline
====================================================

Comprehensive performance tracking and logging system that monitors:
- Individual subprocess execution times
- GPU utilization and memory usage
- Pipeline stage progression
- Resource consumption metrics
- Detailed timing breakdowns
"""

import time
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Any, List, Generator
from contextlib import contextmanager
from datetime import datetime
import threading

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False


class PerformanceTimer:
    """Context manager for timing code blocks with automatic logging"""

    def __init__(self, name: str, logger: 'PerformanceLogger' = None):
        self.name = name
        self.logger = logger
        self.start_time = None
        self.end_time = None
        self.elapsed = None

    def __enter__(self) -> 'PerformanceTimer':
        self.start_time = time.perf_counter()
        if self.logger:
            self.logger.log(f"Starting: {self.name}", level="DEBUG")
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> None:
        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time
        if self.logger:
            self.logger.record_timing(self.name, self.elapsed)
            self.logger.log(f"Completed: {self.name} in {self.elapsed:.3f}s", level="INFO")


class GPUMonitor:
    """Monitor GPU utilization and memory during operations"""

    def __init__(self, interval: float = 0.1):
        self.interval = interval
        self.monitoring = False
        self.thread = None
        self.stats = []
        self.device = None

        if HAS_TORCH:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = "mps"

    def start(self) -> None:
        """Start monitoring GPU in background thread"""
        if not self.device:
            return

        self.monitoring = True
        self.stats = []
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self) -> Dict:
        """Stop monitoring and return statistics"""
        self.monitoring = False
        if self.thread:
            self.thread.join(timeout=1.0)

        if not self.stats:
            return {}

        # Calculate aggregate statistics
        return {
            "device": self.device,
            "samples": len(self.stats),
            "avg_utilization": sum(s.get("utilization", 0) for s in self.stats) / len(self.stats),
            "max_utilization": max(s.get("utilization", 0) for s in self.stats),
            "avg_memory_mb": sum(s.get("memory_mb", 0) for s in self.stats) / len(self.stats),
            "max_memory_mb": max(s.get("memory_mb", 0) for s in self.stats),
        }

    def _monitor_loop(self) -> None:
        """Background monitoring loop"""
        while self.monitoring:
            stats = self._get_gpu_stats()
            if stats:
                self.stats.append(stats)
            time.sleep(self.interval)

    def _get_gpu_stats(self) -> Dict:
        """Get current GPU statistics"""
        stats = {}

        if self.device == "cuda" and HAS_TORCH:
            try:
                stats["utilization"] = torch.cuda.utilization()
                stats["memory_mb"] = torch.cuda.memory_allocated() / 1024 / 1024
                stats["memory_reserved_mb"] = torch.cuda.memory_reserved() / 1024 / 1024
            except:
                pass

        elif self.device == "mps" and HAS_TORCH:
            # MPS doesn't provide detailed stats yet
            stats["device"] = "mps"
            stats["available"] = True

        if HAS_GPUTIL and self.device == "cuda":
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    stats["gpu_util_percent"] = gpu.load * 100
                    stats["gpu_memory_percent"] = gpu.memoryUtil * 100
                    stats["gpu_temp_c"] = gpu.temperature
            except:
                pass

        return stats


class PerformanceLogger:
    """
    Main performance logging class that tracks all pipeline operations

    Features:
    - Hierarchical timing tracking
    - GPU utilization monitoring
    - Memory usage tracking
    - Detailed subprocess timing
    - JSON and human-readable reports
    """

    def __init__(self,
                 name: str = "Pipeline",
                 output_dir: Optional[str] = None,
                 enable_gpu_monitoring: bool = True,
                 verbose: bool = True):

        self.name = name
        self.output_dir = Path(output_dir) if output_dir else Path("outputs/performance_logs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.verbose = verbose
        self.enable_gpu_monitoring = enable_gpu_monitoring

        # Timing data structure
        self.timings = {}
        self.stage_stack = []
        self.current_stage = None

        # Metrics
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "total_duration": None,
            "stages": {},
            "subprocesses": {},
            "gpu_stats": {},
            "memory_stats": {}
        }

        # GPU monitoring
        self.gpu_monitor = GPUMonitor() if enable_gpu_monitoring else None

        # Log buffer for detailed output
        self.log_buffer = []

        # Start timestamp
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def start_pipeline(self) -> None:
        """Mark the start of the pipeline"""
        self.metrics["start_time"] = time.perf_counter()
        self.metrics["start_timestamp"] = datetime.now().isoformat()
        self.log(f"Pipeline '{self.name}' started", level="INFO")

    def end_pipeline(self) -> None:
        """Mark the end of the pipeline and generate reports"""
        self.metrics["end_time"] = time.perf_counter()
        self.metrics["end_timestamp"] = datetime.now().isoformat()
        self.metrics["total_duration"] = self.metrics["end_time"] - self.metrics["start_time"]

        self.log(f"Pipeline completed in {self.metrics['total_duration']:.2f}s", level="INFO")

        # Generate reports
        self.generate_reports()

    def start_stage(self, stage_name: str) -> None:
        """Start tracking a new pipeline stage"""
        stage_data = {
            "name": stage_name,
            "start_time": time.perf_counter(),
            "subprocesses": {},
            "gpu_monitor": None
        }

        # Start GPU monitoring for this stage
        if self.gpu_monitor:
            stage_data["gpu_monitor"] = GPUMonitor()
            stage_data["gpu_monitor"].start()

        self.stage_stack.append(stage_data)
        self.current_stage = stage_data

        self.log(f"[{stage_name}] Stage started", level="INFO")

    def end_stage(self, stage_name: Optional[str] = None) -> None:
        """End tracking of current stage"""
        if not self.stage_stack:
            return

        stage_data = self.stage_stack.pop()

        # Stop GPU monitoring
        if stage_data.get("gpu_monitor"):
            gpu_stats = stage_data["gpu_monitor"].stop()
            stage_data["gpu_stats"] = gpu_stats

        # Calculate duration
        stage_data["end_time"] = time.perf_counter()
        stage_data["duration"] = stage_data["end_time"] - stage_data["start_time"]

        # Store in metrics
        self.metrics["stages"][stage_data["name"]] = {
            "duration": stage_data["duration"],
            "subprocesses": stage_data["subprocesses"],
            "gpu_stats": stage_data.get("gpu_stats", {})
        }

        self.log(f"[{stage_data['name']}] Stage completed in {stage_data['duration']:.3f}s", level="INFO")

        # Update current stage
        self.current_stage = self.stage_stack[-1] if self.stage_stack else None

    def record_subprocess(self, name: str, duration: float, metadata: Optional[Dict] = None) -> None:
        """Record timing for a subprocess"""
        subprocess_data = {
            "duration": duration,
            "timestamp": time.perf_counter(),
            "metadata": metadata or {}
        }

        # Add to current stage if exists
        if self.current_stage:
            self.current_stage["subprocesses"][name] = subprocess_data

        # Also track globally
        if name not in self.metrics["subprocesses"]:
            self.metrics["subprocesses"][name] = []
        self.metrics["subprocesses"][name].append(subprocess_data)

        self.log(f"  [{name}] completed in {duration:.3f}s", level="DEBUG")

    def record_timing(self, name: str, duration: float) -> None:
        """Record a simple timing measurement"""
        if name not in self.timings:
            self.timings[name] = []
        self.timings[name].append(duration)

    @contextmanager
    def timer(self, name: str) -> Generator[PerformanceTimer, None, None]:
        """Context manager for timing operations"""
        timer = PerformanceTimer(name, self)
        with timer:
            yield timer

    @contextmanager
    def subprocess(self, name: str, metadata: Optional[Dict] = None) -> Generator[None, None, None]:
        """Context manager for timing subprocesses"""
        start = time.perf_counter()

        # Track memory before
        memory_before = self._get_memory_usage()

        try:
            yield
        finally:
            duration = time.perf_counter() - start

            # Track memory after
            memory_after = self._get_memory_usage()
            memory_delta = memory_after - memory_before if memory_before else 0

            # Add memory info to metadata
            full_metadata = metadata or {}
            full_metadata["memory_delta_mb"] = memory_delta
            full_metadata["memory_after_mb"] = memory_after

            self.record_subprocess(name, duration, full_metadata)

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"

        self.log_buffer.append(log_entry)

        if self.verbose:
            print(log_entry)

    def _get_memory_usage(self) -> float:
        """Get current process memory usage in MB"""
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        return 0.0

    def generate_reports(self) -> None:
        """Generate performance reports in multiple formats"""
        # Generate JSON report
        json_report = self.generate_json_report()
        json_path = self.output_dir / f"performance_{self.session_id}.json"
        with open(json_path, 'w') as f:
            json.dump(json_report, f, indent=2, default=str)
        self.log(f"JSON report saved to: {json_path}", level="INFO")

        # Generate human-readable report
        text_report = self.generate_text_report()
        text_path = self.output_dir / f"performance_{self.session_id}.txt"
        with open(text_path, 'w') as f:
            f.write(text_report)
        self.log(f"Text report saved to: {text_path}", level="INFO")

        # Generate summary
        self.print_summary()

    def generate_json_report(self) -> Dict:
        """Generate detailed JSON performance report"""
        report = {
            "session_id": self.session_id,
            "pipeline_name": self.name,
            "metrics": self.metrics,
            "timings": self.timings,
            "system_info": self._get_system_info()
        }
        return report

    def generate_text_report(self) -> str:
        """Generate human-readable text report"""
        lines: List[str] = []
        lines.append("=" * 80)
        lines.append(f"Performance Report - {self.name}")
        lines.append(f"Session: {self.session_id}")
        lines.append("=" * 80)
        lines.append("")

        # Overall timing
        if self.metrics.get("total_duration"):
            lines.append(f"Total Duration: {self.metrics['total_duration']:.2f}s")
            lines.append("")

        # Stage breakdown
        if self.metrics.get("stages"):
            lines.append("Stage Breakdown:")
            lines.append("-" * 40)

            total = self.metrics.get("total_duration", 1)
            for stage_name, stage_data in self.metrics["stages"].items():
                duration = stage_data["duration"]
                percentage = (duration / total * 100) if total > 0 else 0
                lines.append(f"  {stage_name:30s} {duration:8.3f}s ({percentage:5.1f}%)")

                # Subprocess breakdown for this stage
                if stage_data.get("subprocesses"):
                    for sub_name, sub_data in stage_data["subprocesses"].items():
                        sub_duration = sub_data["duration"]
                        sub_percentage = (sub_duration / duration * 100) if duration > 0 else 0
                        lines.append(f"    - {sub_name:26s} {sub_duration:8.3f}s ({sub_percentage:5.1f}%)")

                # GPU stats for this stage
                if stage_data.get("gpu_stats") and stage_data["gpu_stats"]:
                    gpu = stage_data["gpu_stats"]
                    lines.append(f"    GPU: {gpu.get('device', 'unknown')} - "
                               f"Util: {gpu.get('avg_utilization', 0):.1f}% "
                               f"Mem: {gpu.get('avg_memory_mb', 0):.1f}MB")

            lines.append("")

        # Top subprocess timings
        if self.metrics.get("subprocesses"):
            lines.append("Top Subprocess Timings:")
            lines.append("-" * 40)

            # Aggregate subprocess timings
            subprocess_totals = {}
            for name, timings_list in self.metrics["subprocesses"].items():
                total_time = sum(t["duration"] for t in timings_list)
                count = len(timings_list)
                avg_time = total_time / count if count > 0 else 0
                subprocess_totals[name] = {
                    "total": total_time,
                    "count": count,
                    "avg": avg_time
                }

            # Sort by total time
            sorted_subs = sorted(subprocess_totals.items(), key=lambda x: x[1]["total"], reverse=True)

            for name, stats in sorted_subs[:10]:  # Top 10
                lines.append(f"  {name:30s} Total: {stats['total']:7.3f}s "
                           f"Count: {stats['count']:3d} Avg: {stats['avg']:7.3f}s")

            lines.append("")

        # Memory statistics
        memory_deltas = []
        for stage_data in self.metrics.get("stages", {}).values():
            for sub_data in stage_data.get("subprocesses", {}).values():
                if "memory_delta_mb" in sub_data.get("metadata", {}):
                    memory_deltas.append(sub_data["metadata"]["memory_delta_mb"])

        if memory_deltas:
            lines.append("Memory Usage:")
            lines.append("-" * 40)
            lines.append(f"  Peak memory delta: {max(memory_deltas):.1f} MB")
            lines.append(f"  Average memory delta: {sum(memory_deltas)/len(memory_deltas):.1f} MB")
            lines.append("")

        # Log buffer (last 20 lines)
        if self.log_buffer:
            lines.append("Recent Log Entries:")
            lines.append("-" * 40)
            for entry in self.log_buffer[-20:]:
                lines.append(f"  {entry}")

        return "\n".join(lines)

    def get_summary(self) -> Dict:
        """Get a summary of performance metrics"""
        summary = {
            "total_duration": self.metrics.get("total_duration", 0),
            "stages": self.metrics.get("stages", {}),
            "session_id": self.session_id,
            "start_timestamp": self.metrics.get("start_timestamp"),
            "end_timestamp": self.metrics.get("end_timestamp"),
        }

        # Add stage percentages
        if summary.get("total_duration") and summary["total_duration"] > 0:
            for stage_name, stage_data in summary["stages"].items():
                stage_data["percentage"] = (stage_data["duration"] / summary["total_duration"]) * 100

        return summary

    def print_summary(self) -> None:
        """Print a brief performance summary"""
        if not self.verbose:
            return

        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)

        if self.metrics.get("total_duration"):
            print(f"Total Time: {self.metrics['total_duration']:.2f}s")

        if self.metrics.get("stages"):
            print("\nStage Timings:")
            total = self.metrics.get("total_duration", 1)

            for stage_name, stage_data in self.metrics["stages"].items():
                duration = stage_data["duration"]
                percentage = (duration / total * 100) if total > 0 else 0
                print(f"  {stage_name:25s} {duration:7.2f}s ({percentage:5.1f}%)")

        print("=" * 60)

    def _get_system_info(self) -> Dict:
        """Get system information for the report"""
        info = {
            "python_version": sys.version,
            "platform": sys.platform,
        }

        if HAS_TORCH:
            info["torch_version"] = torch.__version__
            info["cuda_available"] = torch.cuda.is_available()
            info["mps_available"] = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()

            if torch.cuda.is_available():
                info["cuda_device_count"] = torch.cuda.device_count()
                info["cuda_device_name"] = torch.cuda.get_device_name(0)

        if HAS_PSUTIL:
            info["cpu_count"] = psutil.cpu_count()
            info["memory_total_gb"] = psutil.virtual_memory().total / 1024 / 1024 / 1024

        return info


# Singleton instance for easy access
_global_logger = None

def get_logger(name: str = "Pipeline", **kwargs) -> PerformanceLogger:
    """Get or create the global performance logger"""
    global _global_logger
    if _global_logger is None:
        _global_logger = PerformanceLogger(name=name, **kwargs)
    return _global_logger

def reset_logger() -> None:
    """Reset the global logger"""
    global _global_logger
    _global_logger = None