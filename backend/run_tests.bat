@echo off
REM Run all test suites for the AI-Driven Parametric CAD Workbench
setlocal
call venv\Scripts\activate.bat
echo Running focused pytest regression suites...
python -m pytest test_schemas.py test_ast_security.py test_llm_parser.py test_modify_params.py test_geometry_validation.py test_recompute_validation.py test_auth_projects.py test_universal_archetypes.py test_pipeline.py test_gallery_and_formats.py -v --tb=short
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
echo All test suites completed successfully!
