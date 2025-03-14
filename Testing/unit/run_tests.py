import os

# Run all tests in the Testing directory
os.system("pytest Testing/unit/test_set_configurations.py")
os.system("pytest Testing/unit/test_get_all_ids.py")
os.system("pytest Testing/unit/test_gcp_retrieval.py")
os.system("pytest Testing/unit/test_execute_parser.py")
os.system("pytest Testing/unit/test_execute_finalizer.py")
os.system("pytest Testing/unit/test_execute_pipeline.py")