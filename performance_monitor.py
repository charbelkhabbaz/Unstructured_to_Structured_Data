import time
import psutil
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Data class to store performance metrics."""
    operation_name: str
    start_time: float
    end_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    success: bool = True
    error_message: str = ""
    
    @property
    def duration(self) -> float:
        """Calculate the duration of the operation."""
        return self.end_time - self.start_time
    
    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds."""
        return self.duration * 1000

class PerformanceMonitor:
    """
    Performance monitoring utility to track processing times, cache efficiency, and system performance.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.metrics: List[PerformanceMetrics] = []
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'hit_rate': 0.0
        }
        self.system_stats = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_io': []
        }
        self.monitoring_active = False
        self.monitor_thread = None
    
    def start_operation(self, operation_name: str) -> PerformanceMetrics:
        """
        Start monitoring an operation.
        
        Args:
            operation_name: Name of the operation to monitor
        
        Returns:
            PerformanceMetrics object for tracking
        """
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            memory_usage=psutil.virtual_memory().percent,
            cpu_usage=psutil.cpu_percent()
        )
        return metrics
    
    def end_operation(self, metrics: PerformanceMetrics, success: bool = True, error_message: str = ""):
        """
        End monitoring an operation.
        
        Args:
            metrics: PerformanceMetrics object from start_operation
            success: Whether the operation was successful
            error_message: Error message if operation failed
        """
        metrics.end_time = time.time()
        metrics.success = success
        metrics.error_message = error_message
        metrics.memory_usage = psutil.virtual_memory().percent
        metrics.cpu_usage = psutil.cpu_percent()
        
        self.metrics.append(metrics)
        logger.info(f"Operation '{metrics.operation_name}' completed in {metrics.duration_ms:.2f}ms")
    
    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_stats['hits'] += 1
        self._update_cache_stats()
    
    def record_cache_miss(self):
        """Record a cache miss."""
        self.cache_stats['misses'] += 1
        self._update_cache_stats()
    
    def _update_cache_stats(self):
        """Update cache hit rate."""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        if total > 0:
            self.cache_stats['hit_rate'] = self.cache_stats['hits'] / total
    
    def start_system_monitoring(self, interval: float = 1.0):
        """
        Start monitoring system resources in a background thread.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_system_resources,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("System monitoring started")
    
    def stop_system_monitoring(self):
        """Stop system resource monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("System monitoring stopped")
    
    def _monitor_system_resources(self, interval: float):
        """Background thread for monitoring system resources."""
        while self.monitoring_active:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent()
                self.system_stats['cpu_usage'].append({
                    'timestamp': time.time(),
                    'value': cpu_percent
                })
                
                # Memory usage
                memory_percent = psutil.virtual_memory().percent
                self.system_stats['memory_usage'].append({
                    'timestamp': time.time(),
                    'value': memory_percent
                })
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    self.system_stats['disk_io'].append({
                        'timestamp': time.time(),
                        'read_bytes': disk_io.read_bytes,
                        'write_bytes': disk_io.write_bytes
                    })
                
                # Keep only last 1000 entries to prevent memory bloat
                for stat_type in self.system_stats:
                    if len(self.system_stats[stat_type]) > 1000:
                        self.system_stats[stat_type] = self.system_stats[stat_type][-1000:]
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(interval)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all performance metrics.
        
        Returns:
            Dictionary containing performance summary
        """
        if not self.metrics:
            return {"message": "No performance data available"}
        
        # Calculate statistics
        successful_ops = [m for m in self.metrics if m.success]
        failed_ops = [m for m in self.metrics if not m.success]
        
        durations = [m.duration for m in successful_ops]
        
        summary = {
            'total_operations': len(self.metrics),
            'successful_operations': len(successful_ops),
            'failed_operations': len(failed_ops),
            'success_rate': len(successful_ops) / len(self.metrics) if self.metrics else 0,
            'average_duration_ms': sum(durations) / len(durations) if durations else 0,
            'min_duration_ms': min(durations) if durations else 0,
            'max_duration_ms': max(durations) if durations else 0,
            'total_processing_time_ms': sum(durations) * 1000 if durations else 0,
            'cache_stats': self.cache_stats.copy(),
            'operations_by_type': self._group_operations_by_type(),
            'recent_operations': self._get_recent_operations(10),
            'system_stats': self._get_system_summary()
        }
        
        return summary
    
    def _group_operations_by_type(self) -> Dict[str, Dict[str, Any]]:
        """Group operations by type and calculate statistics."""
        grouped = {}
        
        for metric in self.metrics:
            op_type = metric.operation_name
            if op_type not in grouped:
                grouped[op_type] = {
                    'count': 0,
                    'total_duration_ms': 0,
                    'avg_duration_ms': 0,
                    'success_count': 0,
                    'failure_count': 0
                }
            
            grouped[op_type]['count'] += 1
            grouped[op_type]['total_duration_ms'] += metric.duration_ms
            grouped[op_type]['success_count'] += 1 if metric.success else 0
            grouped[op_type]['failure_count'] += 1 if not metric.success else 0
        
        # Calculate averages
        for op_type in grouped:
            count = grouped[op_type]['count']
            if count > 0:
                grouped[op_type]['avg_duration_ms'] = grouped[op_type]['total_duration_ms'] / count
        
        return grouped
    
    def _get_recent_operations(self, count: int) -> List[Dict[str, Any]]:
        """Get the most recent operations."""
        recent = self.metrics[-count:] if len(self.metrics) > count else self.metrics
        return [
            {
                'operation': m.operation_name,
                'duration_ms': m.duration_ms,
                'success': m.success,
                'timestamp': datetime.fromtimestamp(m.start_time).isoformat(),
                'memory_usage': m.memory_usage,
                'cpu_usage': m.cpu_usage
            }
            for m in recent
        ]
    
    def _get_system_summary(self) -> Dict[str, Any]:
        """Get summary of system resource usage."""
        if not self.system_stats['cpu_usage']:
            return {"message": "No system monitoring data available"}
        
        # CPU usage statistics
        cpu_values = [entry['value'] for entry in self.system_stats['cpu_usage']]
        memory_values = [entry['value'] for entry in self.system_stats['memory_usage']]
        
        return {
            'cpu_usage': {
                'current': cpu_values[-1] if cpu_values else 0,
                'average': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0
            },
            'memory_usage': {
                'current': memory_values[-1] if memory_values else 0,
                'average': sum(memory_values) / len(memory_values) if memory_values else 0,
                'max': max(memory_values) if memory_values else 0,
                'min': min(memory_values) if memory_values else 0
            },
            'monitoring_duration_seconds': time.time() - self.system_stats['cpu_usage'][0]['timestamp'] if self.system_stats['cpu_usage'] else 0
        }
    
    def clear_metrics(self):
        """Clear all stored metrics."""
        self.metrics.clear()
        self.cache_stats = {'hits': 0, 'misses': 0, 'hit_rate': 0.0}
        self.system_stats = {'cpu_usage': [], 'memory_usage': [], 'disk_io': []}
        logger.info("Performance metrics cleared")
    
    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics in various formats.
        
        Args:
            format: Export format ("json", "csv")
        
        Returns:
            Exported metrics as string
        """
        summary = self.get_performance_summary()
        
        if format.lower() == "json":
            import json
            return json.dumps(summary, indent=2, default=str)
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Operation', 'Duration (ms)', 'Success', 'Memory (%)', 'CPU (%)', 'Timestamp'])
            
            # Write data
            for metric in self.metrics:
                writer.writerow([
                    metric.operation_name,
                    f"{metric.duration_ms:.2f}",
                    metric.success,
                    f"{metric.memory_usage:.1f}",
                    f"{metric.cpu_usage:.1f}",
                    datetime.fromtimestamp(metric.start_time).isoformat()
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_operation(operation_name: str):
    """
    Decorator to monitor function performance.
    
    Args:
        operation_name: Name of the operation to monitor
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            metrics = performance_monitor.start_operation(operation_name)
            try:
                result = func(*args, **kwargs)
                performance_monitor.end_operation(metrics, success=True)
                return result
            except Exception as e:
                performance_monitor.end_operation(metrics, success=False, error_message=str(e))
                raise
        return wrapper
    return decorator 