@echo off
REM Run all test suites for the AI-Driven Parametric CAD Workbench
setlocal
call venv\Scripts\activate.bat
echo Running focused pytest regression suites...
python -m pytest test_schemas.py test_ast_security.py test_llm_parser.py test_modify_params.py test_geometry_validation.py test_recompute_validation.py -v --tb=short
if errorlevel 1 exit /b 1
echo.
echo Running Week 1-2 Pipeline Tests...
python test_pipeline.py
if errorlevel 1 exit /b 1
echo.
echo Running Week 3 LLM Integration Tests...
python test_week3_llm.py
if errorlevel 1 exit /b 1
echo.
echo Running Gemini Web2API Integration Tests...
pytest test_gemini_web_client.py
if errorlevel 1 exit /b 1
echo.
echo Running FastAPI Endpoint Tests...
python test_api.py
if errorlevel 1 exit /b 1
echo.
echo Running Master Validation Suite (Weeks 1 to 5)...
python test_all_weeks_1_to_5.py
if errorlevel 1 exit /b 1
echo.
echo All test suites completed successfully!
