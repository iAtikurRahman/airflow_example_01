# AI Agent Instructions for airflow_example_01

## Project Overview
This appears to be a new Apache Airflow project that is in its initial setup phase. The project is intended to demonstrate Airflow workflows and DAGs.

## Project Structure
Currently, the project has minimal structure:
- `README.txt` - Basic project readme (to be expanded)

## Recommended Development Patterns
As this is an Apache Airflow project, future development should follow these patterns:
1. DAGs should be placed in a `dags/` directory
2. Each DAG file should have a clear, descriptive name ending in `_dag.py`
3. Task dependencies should be clearly defined using either:
   - `>>` and `<<` operators
   - `.set_upstream()` and `.set_downstream()` methods
4. DAG IDs should follow a consistent naming convention (e.g., `<department>_<purpose>_dag`)

## Key Workflows
*To be added as development progresses*

## Integration Points
*To be added as external integrations are implemented*

## Project-Specific Conventions
*To be added as conventions are established*

---
Note: This is an initial version of the instructions. As the project develops, this document should be updated to include:
- Specific DAG examples and patterns
- Testing and debugging workflows
- Connection management practices
- Common task patterns and templates
- Environment setup instructions
- Monitoring and alerting configurations