import os

# Run all tests in the Testing directory
os.system("pytest Testing/unit/test_unit_set_configurations.py")
os.system("pytest Testing/unit/test_unit_get_all_ids.py")
os.system("pytest Testing/unit/test_unit_gcp_retrieval.py")
os.system("pytest Testing/unit/test_unit_execute_parser.py")
os.system("pytest Testing/unit/test_unit_execute_finalizer.py")
