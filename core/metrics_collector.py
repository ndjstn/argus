from typing import Dict, Any
import logging
import sqlite3
import os
import psutil
import time
from datetime import datetime
import json

# Local imports
from .database import db_pool, DatabaseError

class MetricsCollector:
    """Collector for system and task metrics"""
    
    def __init__(self, db_path: str = "data/core.db"):
        self.logger = logging.getLogger(__name__)
        self.collect_count = 0
        self.logger.info("Initializing Metrics Collector")
        
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics"""
        start_time = time.time()
        self.collect_count += 1
        
        self.logger.debug("Collecting system metrics", extra={
            "event": "metrics_system_start",
            "collect_count": self.collect_count
        })
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024 * 1024)  # MB
            
            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            
            # Network metrics
            net_io = psutil.net_io_counters()
            network_bytes_sent = net_io.bytes_sent
            network_bytes_recv = net_io.bytes_recv
            
            collect_time = time.time() - start_time
            metrics = {
                "timestamp": time.time(),
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "memory_percent": memory_percent,
                "memory_available_mb": memory_available,
                "disk_percent": disk_percent,
                "network_bytes_sent": network_bytes_sent,
                "network_bytes_recv": network_bytes_recv
            }
            
            self.logger.info("System metrics collected successfully", extra={
                "event": "metrics_system_collected",
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "collect_time_ms": round(collect_time * 1000, 2),
                "collect_count": self.collect_count
            })
            
            return metrics
        except Exception as e:
            collect_time = time.time() - start_time
            self.logger.error("Error collecting system metrics", extra={
                "event": "metrics_system_error",
                "error": str(e),
                "collect_time_ms": round(collect_time * 1000, 2),
                "collect_count": self.collect_count
            })
            return {}
    
    def collect_task_metrics(self, task_id: int, agent: str, tool: str, params: Dict[str, Any],
                           start_time: float, end_time: float, success: bool, error_code: str = None,
                           retries: int = 0, bytes_in: int = 0, bytes_out: int = 0) -> bool:
        """Collect and store task-level metrics"""
        collect_start = time.time()
        self.collect_count += 1
        
        self.logger.debug("Collecting task metrics", extra={
            "event": "metrics_task_start",
            "task_id": task_id,
            "agent": agent,
            "tool": tool,
            "collect_count": self.collect_count
        })
        
        try:
            # Calculate metrics
            latency_ms = (end_time - start_time) * 1000
            cpu_ms = 0  # Would need more detailed tracking to measure this accurately
            mem_mb = 0  # Would need more detailed tracking to measure this accurately
            
            # Store in database
            with db_pool.connection() as conn:
                cursor = conn.cursor()
                
                # Insert run record
                cursor.execute("""
                    INSERT INTO runs (task_id, agent, tool, params_json, start_ts, end_ts, success, error_code, retries,
                                    bytes_in, bytes_out, latency_ms, cpu_ms, mem_mb, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (task_id, agent, tool, json.dumps(params), int(start_time), int(end_time), int(success), error_code, retries,
                      bytes_in, bytes_out, latency_ms, cpu_ms, mem_mb, ""))
                
                conn.commit()
            
            collect_time = time.time() - collect_start
            self.logger.info("Task metrics collected and stored successfully", extra={
                "event": "metrics_task_collected",
                "task_id": task_id,
                "agent": agent,
                "tool": tool,
                "success": success,
                "latency_ms": latency_ms,
                "retries": retries,
                "bytes_in": bytes_in,
                "bytes_out": bytes_out,
                "collect_time_ms": round(collect_time * 1000, 2),
                "collect_count": self.collect_count
            })
            
            return True
        except DatabaseError as e:
            collect_time = time.time() - collect_start
            self.logger.error("Error collecting task metrics due to database error", extra={
                "event": "metrics_task_error",
                "task_id": task_id,
                "agent": agent,
                "tool": tool,
                "error": str(e),
                "error_type": "database",
                "collect_time_ms": round(collect_time * 1000, 2),
                "collect_count": self.collect_count
            })
            return False
        except Exception as e:
            collect_time = time.time() - collect_start
            self.logger.error("Error collecting task metrics due to unexpected error", extra={
                "event": "metrics_task_error",
                "task_id": task_id,
                "agent": agent,
                "tool": tool,
                "error": str(e),
                "error_type": "unexpected",
                "collect_time_ms": round(collect_time * 1000, 2),
                "collect_count": self.collect_count
            })
            return False
    
    def aggregate_daily_metrics(self) -> bool:
        """Aggregate daily metrics from runs table"""
        start_time = time.time()
        self.collect_count += 1
        
        self.logger.debug("Aggregating daily metrics", extra={
            "event": "metrics_daily_start",
            "collect_count": self.collect_count
        })
        
        try:
            with db_pool.connection() as conn:
                cursor = conn.cursor()
                
                # Get today's date
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Aggregate metrics for today
                cursor.execute("""
                    SELECT
                        COUNT(*) as tasks_completed,
                        AVG(success) as success_rate,
                        AVG(latency_ms) as avg_latency_ms,
                        AVG(retries) as avg_retries
                    FROM runs
                    WHERE date(start_ts, 'unixepoch') = ?
                """, (today,))
                
                result = cursor.fetchone()
                
                if result:
                    tasks_completed, success_rate, avg_latency_ms, avg_retries = result
                    
                    # Insert or update daily metrics
                    cursor.execute("""
                        INSERT OR REPLACE INTO metrics_daily (day, tasks_completed, success_rate, avg_latency_ms, avg_retries)
                        VALUES (?, ?, ?, ?, ?)
                    """, (today, tasks_completed or 0, success_rate or 0, avg_latency_ms or 0, avg_retries or 0))
                    
                    conn.commit()
                
            aggregate_time = time.time() - start_time
            self.logger.info("Daily metrics aggregated successfully", extra={
                "event": "metrics_daily_aggregated",
                "day": today,
                "tasks_completed": tasks_completed or 0,
                "success_rate": success_rate or 0,
                "avg_latency_ms": avg_latency_ms or 0,
                "avg_retries": avg_retries or 0,
                "aggregate_time_ms": round(aggregate_time * 1000, 2),
                "collect_count": self.collect_count
            })
            
            return True
        except DatabaseError as e:
            aggregate_time = time.time() - start_time
            self.logger.error("Error aggregating daily metrics due to database error", extra={
                "event": "metrics_daily_error",
                "error": str(e),
                "error_type": "database",
                "aggregate_time_ms": round(aggregate_time * 1000, 2),
                "collect_count": self.collect_count
            })
            return False
        except Exception as e:
            aggregate_time = time.time() - start_time
            self.logger.error("Error aggregating daily metrics due to unexpected error", extra={
                "event": "metrics_daily_error",
                "error": str(e),
                "error_type": "unexpected",
                "aggregate_time_ms": round(aggregate_time * 1000, 2),
                "collect_count": self.collect_count
            })
            return False
    
    def collect_training_example(self, agent: str, tool: str, features: Dict[str, Any],
                               success: bool, latency_ms: int) -> bool:
        """Collect a training example for the learning loop"""
        start_time = time.time()
        self.collect_count += 1
        
        self.logger.debug("Collecting training example", extra={
            "event": "metrics_training_start",
            "agent": agent,
            "tool": tool,
            "collect_count": self.collect_count
        })
        
        try:
            with db_pool.connection() as conn:
                cursor = conn.cursor()
                
                # Insert training example
                cursor.execute("""
                    INSERT INTO train_examples (agent, tool, feature_json, label_success, label_latency_ms, created_ts)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (agent, tool, json.dumps(features), int(success), latency_ms, int(time.time())))
                
                conn.commit()
            
            collect_time = time.time() - start_time
            self.logger.info("Training example collected and stored successfully", extra={
                "event": "metrics_training_collected",
                "agent": agent,
                "tool": tool,
                "success": success,
                "latency_ms": latency_ms,
                "feature_count": len(features) if features else 0,
                "collect_time_ms": round(collect_time * 1000, 2),
                "collect_count": self.collect_count
            })
            
            return True
        except DatabaseError as e:
            collect_time = time.time() - start_time
            self.logger.error("Error collecting training example due to database error", extra={
                "event": "metrics_training_error",
                "agent": agent,
                "tool": tool,
                "error": str(e),
                "error_type": "database",
                "collect_time_ms": round(collect_time * 1000, 2),
                "collect_count": self.collect_count
            })
            return False
        except Exception as e:
            collect_time = time.time() - start_time
            self.logger.error("Error collecting training example due to unexpected error", extra={
                "event": "metrics_training_error",
                "agent": agent,
                "tool": tool,
                "error": str(e),
                "error_type": "unexpected",
                "collect_time_ms": round(collect_time * 1000, 2),
                "collect_count": self.collect_count
            })
            return False
            
    def get_metrics_info(self) -> Dict[str, Any]:
        """Get information about the metrics collector for monitoring"""
        return {
            "collect_count": self.collect_count
        }

if __name__ == "__main__":
    # For testing purposes
    collector = MetricsCollector()
    
    # Collect system metrics
    system_metrics = collector.collect_system_metrics()
    print(f"System metrics: {system_metrics}")
    
    # Collect task metrics (example)
    task_success = collector.collect_task_metrics(
        task_id=1,
        agent="browser",
        tool="playwright",
        params={"timeout": 15},
        start_time=time.time() - 5,  # 5 seconds ago
        end_time=time.time(),
        success=True,
        retries=0,
        bytes_in=1024,
        bytes_out=2048
    )
    print(f"Task metrics collection: {'Success' if task_success else 'Failed'}")
    
    # Aggregate daily metrics
    daily_success = collector.aggregate_daily_metrics()
    print(f"Daily metrics aggregation: {'Success' if daily_success else 'Failed'}")