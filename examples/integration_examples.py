"""
Integration Examples - Complete Validation Pipeline
Week 5 Day 4

Demonstrates:
1. Basic validation workflow
2. Batch processing
3. Error handling scenarios
4. Review queue integration
5. Performance monitoring
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation.integrated_validation_pipeline import (
    IntegratedValidationPipeline,
    ValidationDecision,
    validate_answer
)
from unittest.mock import Mock, MagicMock
import json


def setup_mock_db():
    """Setup mock database for examples"""
    mock_db = Mock()
    mock_result = MagicMock()
    mock_result.interpretation_type = "NARROW"
    mock_result.authority_level = "BINDING"
    mock_result.boost_factor = 2.5
    mock_result.confidence = 0.95
    mock_db.execute.return_value.fetchone.return_value = mock_result
    return mock_db


def example_1_basic_workflow():
    """
    Example 1: Basic validation workflow
    """
    print("=" * 80)
    print("EXAMPLE 1: Basic Validation Workflow")
    print("=" * 80)
    
    # Initialize pipeline
    mock_db = setup_mock_db()
    pipeline = IntegratedValidationPipeline(db_session=mock_db)
    
    # Sample answer
    answer = """
    **Statute:** Misrepresentation Act, Section 2 states "No person shall be liable 
    for misrepresentation unless there was a duty to disclose."
    
    **Judicial Interpretation:** In Wee Chiaw Sek Anna v Ng Li-Ann Genevieve 
    [2013] SGCA 36, ¶158, the Court held that Section 2 applies only to fiduciary 
    relationships where a duty of disclosure exists.
    
    **Synthesis:** While the statute appears to apply broadly, case law has limited 
    it to trust-based relationships.
    
    **Practical Effect:** In practice, silence is only misrepresentation in fiduciary 
    contexts like trustee-beneficiary relationships.
    """
    
    # Validate
    print("\n🔍 Validating answer...")
    result = pipeline.validate(answer)
    
    # Display results
    print(f"\n📊 VALIDATION RESULT:")
    print(f"  Decision: {result.decision.value.upper()}")
    print(f"  Priority: {result.priority or 'N/A'}")
    
    print(f"\n⏱️  PERFORMANCE:")
    print(f"  Total Time: {result.metrics.total_time_ms:.2f}ms")
    print(f"  Synthesis: {result.metrics.synthesis_time_ms:.2f}ms")
    print(f"  Hallucination: {result.metrics.hallucination_time_ms:.2f}ms")
    
    print(f"\n📈 SCORES:")
    print(f"  Synthesis Quality: {result.metrics.synthesis_score:.2f}")
    print(f"  Hallucination Rate: {result.metrics.hallucination_rate:.1%}")
    
    print(f"\n💬 FEEDBACK:")
    for fb in result.feedback:
        print(f"  • {fb}")
    
    # Routing decision
    print(f"\n🎯 ROUTING:")
    if result.decision == ValidationDecision.PASS:
        print("  ✅ SEND TO USER")
    elif result.decision == ValidationDecision.REVIEW:
        print(f"  ⚠️ SEND TO REVIEW QUEUE (Priority: {result.priority})")
    else:
        print("  ❌ REJECT - Do not show to user")
    
    print("\n")


def example_2_batch_processing():
    """
    Example 2: Batch processing multiple answers
    """
    print("=" * 80)
    print("EXAMPLE 2: Batch Processing")
    print("=" * 80)
    
    mock_db = setup_mock_db()
    pipeline = IntegratedValidationPipeline(db_session=mock_db)
    
    # Multiple answers to validate
    answers = [
        {
            'answer': 'Perfect answer with all 4 sections...',
            'query': 'What is the test for misrepresentation?',
            'context': {}
        },
        {
            'answer': 'Weak answer.',
            'query': 'When does silence amount to misrepresentation?',
            'context': {}
        },
        {
            'answer': 'Medium quality answer with some sections...',
            'query': 'What are the requirements for striking out?',
            'context': {}
        },
    ]
    
    print(f"\n🔄 Processing {len(answers)} answers...")
    results = pipeline.validate_batch(answers)
    
    # Display summary
    print(f"\n📊 BATCH RESULTS:")
    for i, result in enumerate(results, 1):
        print(f"\n  Answer {i}:")
        print(f"    Decision: {result.decision.value}")
        print(f"    Synthesis: {result.metrics.synthesis_score:.2f}")
        print(f"    Time: {result.metrics.total_time_ms:.1f}ms")
    
    # Compute statistics
    stats = pipeline.get_statistics(results)
    
    print(f"\n📈 STATISTICS:")
    print(f"  Total: {stats['total']}")
    print(f"  Passed: {stats['passed']} ({stats['pass_rate']:.1%})")
    print(f"  Review: {stats['review']} ({stats['review_rate']:.1%})")
    print(f"  Rejected: {stats['rejected']} ({stats['reject_rate']:.1%})")
    print(f"  Avg Time: {stats['avg_time_ms']:.2f}ms")
    print(f"  Avg Synthesis: {stats['avg_synthesis_score']:.2f}")
    print("\n")


def example_3_error_handling():
    """
    Example 3: Error handling and graceful degradation
    """
    print("=" * 80)
    print("EXAMPLE 3: Error Handling & Graceful Degradation")
    print("=" * 80)
    
    # Test without database connection
    print("\n🔧 Scenario: No database connection")
    pipeline_no_db = IntegratedValidationPipeline(
        db_session=None,
        enable_hallucination=False  # Disable hallucination detection
    )
    
    answer = "Some legal answer about defamation."
    result = pipeline_no_db.validate(answer)
    
    print(f"  Decision: {result.decision.value}")
    print(f"  Warnings: {len(result.warnings)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Stages Completed: {result.metrics.stages_completed}")
    print(f"  Stages Failed: {result.metrics.stages_failed}")
    
    # Test with malformed input
    print("\n🔧 Scenario: Empty answer")
    mock_db = setup_mock_db()
    pipeline = IntegratedValidationPipeline(db_session=mock_db)
    result = pipeline.validate("")
    
    print(f"  Decision: {result.decision.value}")
    print(f"  Synthesis Score: {result.metrics.synthesis_score:.2f}")
    
    # Test with very long answer
    print("\n🔧 Scenario: Very long answer (stress test)")
    long_answer = "Legal text. " * 500  # 1000 words
    result = pipeline.validate(long_answer)
    
    print(f"  Decision: {result.decision.value}")
    print(f"  Processing Time: {result.metrics.total_time_ms:.1f}ms")
    print("\n")


def example_4_review_queue_integration():
    """
    Example 4: Integration with review queue
    """
    print("=" * 80)
    print("EXAMPLE 4: Review Queue Integration")
    print("=" * 80)
    
    mock_db = setup_mock_db()
    pipeline = IntegratedValidationPipeline(db_session=mock_db)
    
    # Simulate review queue
    review_queue = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': []
    }
    
    # Process multiple answers
    test_answers = [
        ("Perfect answer with all sections", 0.85, 0.0),
        ("Weak answer", 0.45, 0.0),
        ("Medium answer", 0.70, 0.0),
        ("Bad answer with hallucination", 0.60, 0.15),
    ]
    
    print("\n🔄 Processing answers and routing to queues...")
    
    for answer_text, expected_synth, expected_hall in test_answers:
        result = pipeline.validate(answer_text)
        
        if result.decision == ValidationDecision.PASS:
            print(f"  ✅ PASS: {answer_text[:30]}...")
        elif result.decision == ValidationDecision.REVIEW:
            priority = result.priority or 'medium'
            review_queue[priority].append(result)
            print(f"  ⚠️ REVIEW ({priority}): {answer_text[:30]}...")
        else:
            print(f"  ❌ REJECT: {answer_text[:30]}...")
    
    # Display review queue status
    print(f"\n📋 REVIEW QUEUE STATUS:")
    for priority in ['critical', 'high', 'medium', 'low']:
        count = len(review_queue[priority])
        print(f"  {priority.upper()}: {count} item(s)")
    
    print("\n")


def example_5_performance_monitoring():
    """
    Example 5: Performance monitoring and logging
    """
    print("=" * 80)
    print("EXAMPLE 5: Performance Monitoring")
    print("=" * 80)
    
    mock_db = setup_mock_db()
    pipeline = IntegratedValidationPipeline(db_session=mock_db)
    
    # Validate and collect metrics
    answer = "Sample legal answer for performance testing."
    
    print("\n📊 Running 10 validations to collect metrics...")
    
    results = []
    for i in range(10):
        result = pipeline.validate(answer)
        results.append(result)
    
    # Analyze performance
    times = [r.metrics.total_time_ms for r in results]
    synthesis_times = [r.metrics.synthesis_time_ms for r in results]
    
    print(f"\n⏱️  TIMING ANALYSIS:")
    print(f"  Total Time:")
    print(f"    Mean: {sum(times) / len(times):.2f}ms")
    print(f"    Min: {min(times):.2f}ms")
    print(f"    Max: {max(times):.2f}ms")
    
    print(f"\n  Synthesis Time:")
    print(f"    Mean: {sum(synthesis_times) / len(synthesis_times):.2f}ms")
    
    # Check against targets
    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(0.95 * len(times))]
    
    print(f"\n🎯 TARGET VALIDATION:")
    print(f"  Avg < 50ms: {avg_time:.2f}ms {'✅' if avg_time < 50 else '⚠️'}")
    print(f"  P95 < 100ms: {p95_time:.2f}ms {'✅' if p95_time < 100 else '⚠️'}")
    
    print("\n")


def example_6_json_export():
    """
    Example 6: JSON export for API integration
    """
    print("=" * 80)
    print("EXAMPLE 6: JSON Export for API")
    print("=" * 80)
    
    mock_db = setup_mock_db()
    pipeline = IntegratedValidationPipeline(db_session=mock_db)
    
    answer = """
    **Statute:** Defamation Act, Section 7
    **Interpretation:** Court held requirements in Lim [2015] SGCA 33
    **Synthesis:** Statute is limited by case law
    **Practical Effect:** High bar for defense
    """
    
    result = pipeline.validate(answer)
    
    # Export as JSON
    result_json = json.dumps(result.to_dict(), indent=2)
    
    print("\n📤 JSON OUTPUT:")
    print(result_json)
    
    print("\n💡 API INTEGRATION EXAMPLE:")
    print("""
    @app.post("/validate")
    def validate_endpoint(request: ValidateRequest):
        result = pipeline.validate(request.answer, request.query, request.context)
        return result.to_dict()
    """)
    
    print("\n")


def main():
    """Run all examples"""
    print("\n🚀 INTEGRATED VALIDATION PIPELINE - EXAMPLES\n")
    
    example_1_basic_workflow()
    example_2_batch_processing()
    example_3_error_handling()
    example_4_review_queue_integration()
    example_5_performance_monitoring()
    example_6_json_export()
    
    print("=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)


if __name__ == '__main__':
    main()
