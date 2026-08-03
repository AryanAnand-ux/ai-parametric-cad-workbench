@echo off
REM Run all test suites for the AI-Driven Parametric CAD Workbench
echo Running Week 1-2 Pipeline Tests...
call venv\Scripts\activate.bat
python test_pipeline.py
echo.
echo Running Week 3 LLM Integration Tests...
python test_week3_llm.py
echo.
echo Running FastAPI Endpoint Tests...
python test_api.py
echo.
echo All tests complete!
