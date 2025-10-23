"""
Performance Benchmarks for Validation Pipeline
Week 5 Day 4

Measures:
- End-to-end latency (p50, p95, p99)
- Throughput (answers/second)
- Per-stage timing
- Resource utilization
"""

import time
import statistics
from typing import List, Dict
from dataclasses import dataclass
import json

from validation.integrated_validation_pipeline import (
    IntegratedValidationPipeline,
    ValidationResult
)


@dataclass
class BenchmarkResult:
    """Results from a benchmark run"""
    total_samples: int
    total_time_seconds: float
    throughput_per_second: float
    
    # Latency metrics (ms)
    latency_mean_ms: float
    latency_median_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    latency_min_ms: float
    latency_max_ms: float
    
    # Per-stage timing
    synthesis_mean_ms: float
    citation_mean_ms: float
    hallucination_mean_ms: float
    
    # Decision breakdown
    passed_count: int
    review_count: int
    rejected_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'summary': {
                'samples': self.total_samples,
                'duration_seconds': round(self.total_time_seconds, 2),
                'throughput': round(self.throughput_per_second, 2)
            },
            'latency_ms': {
                'mean': round(self.latency_mean_ms, 2),
                'median': round(self.latency_median_ms, 2),
                'p95': round(self.latency_p95_ms, 2),
                'p99': round(self.latency_p99_ms, 2),
                'min': round(self.latency_min_ms, 2),
                'max': round(self.latency_max_ms, 2)
            },
            'stage_timing_ms': {
                'synthesis': round(self.synthesis_mean_ms, 2),
                'citation': round(self.citation_mean_ms, 2),
                'hallucination': round(self.hallucination_mean_ms, 2)
            },
            'decisions': {
                'passed': self.passed_count,
                'review': self.review_count,
                'rejected': self.rejected_count,
                'pass_rate': round(self.passed_count / self.total_samples, 3)
            }
        }
    
    def print_report(self):
        """Print human-readable benchmark report"""
        print("\n" + "=" * 80)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)
        
        print(f"\n📊 SUMMARY")
        print(f"  Samples: {self.total_samples}")
        print(f"  Duration: {self.total_time_seconds:.2f}s")
        print(f"  Throughput: {self.throughput_per_second:.2f} answers/second")
        
        print(f"\n⏱️  LATENCY (milliseconds)")
        print(f"  Mean:   {self.latency_mean_ms:.2f} ms")
        print(f"  Median: {self.latency_median_ms:.2f} ms")
        print(f"  P95:    {self.latency_p95_ms:.2f} ms {'✅' if self.latency_p95_ms < 100 else '⚠️ SLOW'}")
        print(f"  P99:    {self.latency_p99_ms:.2f} ms")
        print(f"  Min:    {self.latency_min_ms:.2f} ms")
        print(f"  Max:    {self.latency_max_ms:.2f} ms")
        
        print(f"\n🔧 PER-STAGE TIMING (mean)")
        print(f"  Synthesis:     {self.synthesis_mean_ms:.2f} ms")
        print(f"  Citation:      {self.citation_mean_ms:.2f} ms")
        print(f"  Hallucination: {self.hallucination_mean_ms:.2f} ms")
        
        print(f"\n✅ DECISIONS")
        print(f"  Passed:   {self.passed_count} ({self.passed_count/self.total_samples:.1%})")
        print(f"  Review:   {self.review_count} ({self.review_count/self.total_samples:.1%})")
        print(f"  Rejected: {self.rejected_count} ({self.rejected_count/self.total_samples:.1%})")
        
        print("\n" + "=" * 80)


class ValidationBenchmark:
    """
    Benchmark tool for validation pipeline.
    
    Usage:
        benchmark = ValidationBenchmark()
        result = benchmark.run(sample_answers, iterations=100)
        result.print_report()
    """
    
    def __init__(self, db_session=None):
        """Initialize benchmark tool"""
        self.pipeline = IntegratedValidationPipeline(db_session=db_session)
    
    def run(
        self,
        test_answers: List[str],
        iterations: int = 100,
        warmup: int = 10
    ) -> BenchmarkResult:
        """
        Run benchmark on test answers.
        
        Args:
            test_answers: List of answers to validate
            iterations: Number of iterations to run
            warmup: Number of warmup iterations (not measured)
            
        Returns:
            BenchmarkResult with detailed metrics
        """
        print(f"\n🚀 Starting benchmark: {iterations} iterations + {warmup} warmup")
        
        # Warmup phase
        print(f"   Warming up... ({warmup} iterations)")
        for i in range(warmup):
            answer = test_answers[i % len(test_answers)]
            _ = self.pipeline.validate(answer)
        
        # Measurement phase
        print(f"   Measuring... ({iterations} iterations)")
        results: List[ValidationResult] = []
        start_time = time.time()
        
        for i in range(iterations):
            answer = test_answers[i % len(test_answers)]
            result = self.pipeline.validate(answer)
            results.append(result)
            
            if (i + 1) % 20 == 0:
                print(f"   Progress: {i + 1}/{iterations}")
        
        total_time = time.time() - start_time
        
        # Compute metrics
        return self._compute_metrics(results, total_time)
    
    def _compute_metrics(
        self,
        results: List[ValidationResult],
        total_time: float
    ) -> BenchmarkResult:
        """Compute benchmark metrics from results"""
        
        # Extract latencies
        latencies = [r.metrics.total_time_ms for r in results]
        latencies_sorted = sorted(latencies)
        
        n = len(latencies)
        p95_idx = int(0.95 * n)
        p99_idx = int(0.99 * n)
        
        # Extract per-stage times
        synthesis_times = [r.metrics.synthesis_time_ms for r in results]
        citation_times = [r.metrics.citation_time_ms for r in results]
        hallucination_times = [r.metrics.hallucination_time_ms for r in results]
        
        # Count decisions
        from validation.integrated_validation_pipeline import ValidationDecision
        passed = sum(1 for r in results if r.decision == ValidationDecision.PASS)
        review = sum(1 for r in results if r.decision == ValidationDecision.REVIEW)
        rejected = sum(1 for r in results if r.decision == ValidationDecision.REJECT)
        
        return BenchmarkResult(
            total_samples=n,
            total_time_seconds=total_time,
            throughput_per_second=n / total_time,
            latency_mean_ms=statistics.mean(latencies),
            latency_median_ms=statistics.median(latencies),
            latency_p95_ms=latencies_sorted[p95_idx] if p95_idx < n else latencies_sorted[-1],
            latency_p99_ms=latencies_sorted[p99_idx] if p99_idx < n else latencies_sorted[-1],
            latency_min_ms=min(latencies),
            latency_max_ms=max(latencies),
            synthesis_mean_ms=statistics.mean(synthesis_times),
            citation_mean_ms=statistics.mean(citation_times),
            hallucination_mean_ms=statistics.mean(hallucination_times),
            passed_count=passed,
            review_count=review,
            rejected_count=rejected
        )
    
    def run_stress_test(
        self,
        test_answers: List[str],
        target_qps: int = 100,
        duration_seconds: int = 60
    ) -> Dict:
        """
        Run stress test at target QPS (queries per second).
        
        Args:
            test_answers: Test answers to cycle through
            target_qps: Target queries per second
            duration_seconds: How long to run test
            
        Returns:
            Dictionary with stress test results
        """
        print(f"\n🔥 Stress test: {target_qps} QPS for {duration_seconds}s")
        
        interval = 1.0 / target_qps  # Time between queries
        end_time = time.time() + duration_seconds
        
        results = []
        query_count = 0
        start_time = time.time()
        
        while time.time() < end_time:
            query_start = time.time()
            
            # Run validation
            answer = test_answers[query_count % len(test_answers)]
            result = self.pipeline.validate(answer)
            results.append(result)
            query_count += 1
            
            # Sleep to maintain target QPS
            elapsed = time.time() - query_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            if query_count % 100 == 0:
                print(f"   Processed: {query_count} queries")
        
        actual_duration = time.time() - start_time
        actual_qps = query_count / actual_duration
        
        # Compute metrics
        latencies = [r.metrics.total_time_ms for r in results]
        
        return {
            'target_qps': target_qps,
            'actual_qps': round(actual_qps, 2),
            'duration_seconds': round(actual_duration, 2),
            'total_queries': query_count,
            'mean_latency_ms': round(statistics.mean(latencies), 2),
            'p95_latency_ms': round(sorted(latencies)[int(0.95 * len(latencies))], 2),
            'success': actual_qps >= target_qps * 0.9  # Within 10% of target
        }


# Sample test answers for benchmarking
SAMPLE_ANSWERS = [
    # Good answer
    """
    **Statute:** Misrepresentation Act, Section 2
    **Interpretation:** In Wee [2013] SGCA 36, ¶158, the Court held Section 2 applies to fiduciary contexts.
    **Synthesis:** While the statute appears broad, case law has limited it to trust relationships.
    **Practical Effect:** Silence is only misrepresentation in fiduciary contexts.
    """,
    
    # Medium answer
    """
    **Statute:** Defamation Act, Section 7
    **Interpretation:** Court held in Lim [2015] SGCA 33 about public benefit.
    **Synthesis:** The statute is limited by case law.
    """,
    
    # Weak answer
    "The law says something about defamation.",
    
    # Another good answer
    """
    **Statute:** Rules of Court, Order 9 Rule 16 allows striking out claims.
    **Interpretation:** Gabriel Peter [1997] SGCA 58 held this applies only to obviously unsustainable claims.
    **Synthesis:** While the rule appears broad, courts apply it narrowly.
    **Practical Effect:** Claims are rarely struck out at this stage.
    """,
]


def run_standard_benchmark():
    """Run standard benchmark suite"""
    print("\n" + "=" * 80)
    print("VALIDATION PIPELINE - STANDARD BENCHMARK")
    print("=" * 80)
    
    benchmark = ValidationBenchmark()
    
    # Test 1: Latency benchmark
    print("\n📊 TEST 1: Latency Benchmark (100 iterations)")
    result = benchmark.run(SAMPLE_ANSWERS, iterations=100, warmup=10)
    result.print_report()
    
    # Save results
    with open('benchmark_results.json', 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    print("\n💾 Results saved to: benchmark_results.json")
    
    # Test 2: Stress test
    print("\n📊 TEST 2: Stress Test (50 QPS for 10 seconds)")
    stress_result = benchmark.run_stress_test(
        SAMPLE_ANSWERS,
        target_qps=50,
        duration_seconds=10
    )
    
    print(f"\n   Target QPS: {stress_result['target_qps']}")
    print(f"   Actual QPS: {stress_result['actual_qps']}")
    print(f"   Mean Latency: {stress_result['mean_latency_ms']} ms")
    print(f"   P95 Latency: {stress_result['p95_latency_ms']} ms")
    print(f"   Status: {'✅ PASS' if stress_result['success'] else '❌ FAIL'}")
    
    # Check against targets
    print("\n" + "=" * 80)
    print("TARGET VALIDATION")
    print("=" * 80)
    print(f"✅ P95 Latency < 100ms: {result.latency_p95_ms:.2f}ms {'✅ PASS' if result.latency_p95_ms < 100 else '❌ FAIL'}")
    print(f"✅ Throughput > 50/s: {result.throughput_per_second:.2f}/s {'✅ PASS' if result.throughput_per_second > 50 else '❌ FAIL'}")
    print("=" * 80)


if __name__ == '__main__':
    run_standard_benchmark()
