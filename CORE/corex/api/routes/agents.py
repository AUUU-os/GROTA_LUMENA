from fastapi import APIRouter, HTTPException, Body
from typing import List
from modules.omni_extractor.module import omni_extractor, ExtractionRequest, ExtractionResult

router = APIRouter()

@router.post(
    "/omni-extractor/invoke",
    response_model=List[ExtractionResult],
    tags=["agents"]
)
async def invoke_omni_extractor(request: ExtractionRequest):
    """
    Invoke the Omni-Extractor agent to analyze external tools.
    """
    try:
        results = await omni_extractor.execute("invoke", request)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
