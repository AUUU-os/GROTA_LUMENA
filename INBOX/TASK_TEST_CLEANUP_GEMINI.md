# TASK TEST CLEANUP
## DLA: GEMINI_ARCHITECT
## OD: SHAD
## PRIORYTET: HIGH
## OPIS: Pytest zbiera site-packages. Uruchamiaj tylko testy projektu.
## KOMENDA:
cd E:\[runtime]core-x-agent
pytest -sv corex --cov=corex --cov-report=term --cov-report=xml

# Alternatywnie jeśli masz tests/
# pytest -sv tests --cov=corex --cov-report=term --cov-report=xml
