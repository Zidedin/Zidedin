"""Interview preparation resources for Data Engineer roles."""

COMMON_TOPICS = {
    "SQL": {
        "key_areas": [
            "Window functions (ROW_NUMBER, RANK, LAG, LEAD, NTILE)",
            "CTEs and recursive CTEs",
            "Query optimization and execution plans",
            "Indexing strategies (B-tree, Hash, GiST)",
            "Partitioning and sharding",
            "ACID properties and transaction isolation levels",
            "Slowly Changing Dimensions (SCD Types 1, 2, 3)",
        ],
        "sample_questions": [
            "Write a query to find the second highest salary in each department",
            "Explain the difference between RANK, DENSE_RANK, and ROW_NUMBER",
            "How would you optimize a query that joins 5 large tables?",
            "Design a schema for a SCD Type 2 dimension table",
            "Write a query to detect gaps in a time series",
        ],
    },
    "Python": {
        "key_areas": [
            "Generators and iterators for memory-efficient processing",
            "Decorators and context managers",
            "Concurrent programming (threading, multiprocessing, asyncio)",
            "Data processing with pandas / polars",
            "Testing with pytest",
            "Type hints and dataclasses",
        ],
        "sample_questions": [
            "How would you process a 50GB CSV file that doesn't fit in memory?",
            "Explain GIL and its impact on multithreading",
            "Write a decorator that retries a function N times with exponential backoff",
            "What's the difference between deepcopy and shallow copy?",
            "How do you handle schema validation in a data pipeline?",
        ],
    },
    "Data Pipelines": {
        "key_areas": [
            "ETL vs ELT patterns",
            "Batch vs streaming architectures",
            "Data quality and validation frameworks",
            "Orchestration (Airflow, Dagster, Prefect)",
            "Change Data Capture (CDC)",
            "Idempotency and exactly-once processing",
            "Backfilling strategies",
        ],
        "sample_questions": [
            "Design a pipeline that ingests data from 10 different APIs daily",
            "How do you handle late-arriving data in a streaming pipeline?",
            "Explain how you'd implement data quality checks at each pipeline stage",
            "What's your approach to pipeline monitoring and alerting?",
            "How do you handle schema evolution in a data lake?",
        ],
    },
    "Cloud & Infrastructure": {
        "key_areas": [
            "AWS: S3, Glue, Redshift, Lambda, Kinesis, EMR, Step Functions",
            "GCP: BigQuery, Dataflow, Cloud Composer, Pub/Sub, Cloud Functions",
            "Infrastructure as Code (Terraform, CloudFormation)",
            "Container orchestration (Kubernetes, ECS)",
            "CI/CD pipelines for data infrastructure",
            "Cost optimization strategies",
        ],
        "sample_questions": [
            "Design a data lake architecture on AWS/GCP",
            "How would you migrate an on-prem data warehouse to the cloud?",
            "Explain your approach to managing Terraform state in a team",
            "How do you handle secrets management in data pipelines?",
            "Design a multi-region disaster recovery strategy for a data platform",
        ],
    },
    "System Design": {
        "key_areas": [
            "Data modeling (star schema, snowflake, data vault)",
            "Distributed systems fundamentals (CAP theorem, consensus)",
            "Message queues and event streaming (Kafka, RabbitMQ)",
            "Data lake vs data warehouse vs lakehouse",
            "Real-time analytics architectures (Lambda, Kappa)",
            "Data mesh and data products",
        ],
        "sample_questions": [
            "Design a real-time analytics dashboard for an e-commerce platform",
            "How would you build a feature store for an ML team?",
            "Design a data platform that handles 1TB of new data daily",
            "How would you implement a data catalog and lineage system?",
            "Design a CDC pipeline from a transactional DB to a data warehouse",
        ],
    },
    "Behavioral": {
        "key_areas": [
            "STAR method (Situation, Task, Action, Result)",
            "Technical leadership examples",
            "Cross-team collaboration",
            "Handling ambiguity and changing requirements",
            "Mentoring and knowledge sharing",
        ],
        "sample_questions": [
            "Tell me about a time you had to debug a complex data pipeline failure in production",
            "Describe a situation where you had to push back on a technical decision",
            "How do you prioritize when multiple teams need data engineering support?",
            "Tell me about a project where requirements changed significantly mid-way",
            "How do you stay current with data engineering trends and technologies?",
        ],
    },
}


def get_study_plan(weeks=4):
    """Generate a study plan distributed over N weeks."""
    topics = list(COMMON_TOPICS.keys())
    plan = {}
    for i in range(weeks):
        week_topics = []
        for j, topic in enumerate(topics):
            if j % weeks == i % weeks or (i == weeks - 1):
                week_topics.append(topic)
        plan[f"Week {i + 1}"] = week_topics[:3]
    return plan


def get_topic_details(topic):
    """Get detailed preparation info for a specific topic."""
    return COMMON_TOPICS.get(topic)


def format_prep_guide():
    """Format a complete interview preparation guide."""
    lines = ["# Data Engineer Interview Preparation Guide\n"]
    for topic, details in COMMON_TOPICS.items():
        lines.append(f"\n## {topic}\n")
        lines.append("### Key Areas:")
        for area in details["key_areas"]:
            lines.append(f"  - {area}")
        lines.append("\n### Practice Questions:")
        for q in details["sample_questions"]:
            lines.append(f"  - {q}")
    return "\n".join(lines)
