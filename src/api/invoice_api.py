#!/usr/bin/env python3
"""
Invoice Generator API - FastAPI Implementation
Clean API design for invoice generation service
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import base64
import io
import tempfile
import uuid
from pathlib import Path
from datetime import datetime

# Import our clean invoice generator
from .core_clean_example import InvoiceGenerator, InvoiceConfig, InvoiceResult

app = FastAPI(
    title="Invoice Generator API",
    description="Generate Excel invoices from JSON data",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Request/Response Models
class InvoiceOptions(BaseModel):
    """Invoice generation options"""
    enable_daf: bool = False
    enable_custom: bool = False
    sheets: Optional[List[str]] = None
    print_settings: Optional[Dict[str, Any]] = None
    verbose: bool = True

class InvoiceRequest(BaseModel):
    """JSON payload request model"""
    invoice_data: Dict[str, Any] = Field(..., description="Invoice data structure")
    template_type: Optional[str] = Field(None, description="Template type (e.g., CLW, BRO)")
    options: Optional[InvoiceOptions] = None

class InvoiceResponse(BaseModel):
    """Successful response model"""
    success: bool = True
    request_id: str
    result: Dict[str, Any]
    metadata: Dict[str, Any]
    warnings: List[str] = []

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    request_id: str
    error: Dict[str, Any]
    processing_time: float

# API Endpoints

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Invoice Generator API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/templates")
async def list_templates():
    """List available templates"""
    template_dir = Path("src/invoice_generator/TEMPLATE")
    if not template_dir.exists():
        raise HTTPException(status_code=500, detail="Template directory not found")
    
    templates = []
    for template_file in template_dir.glob("*.xlsx"):
        templates.append({
            "name": template_file.stem,
            "filename": template_file.name,
            "size": template_file.stat().st_size
        })
    
    return {
        "templates": templates,
        "count": len(templates)
    }

@app.post("/api/v1/invoice/generate", response_model=InvoiceResponse)
async def generate_invoice_json(request: InvoiceRequest):
    """Generate invoice from JSON payload"""
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    try:
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_input:
            json.dump(request.invoice_data, temp_input, indent=2)
            input_path = Path(temp_input.name)
        
        # Generate invoice
        result = await _generate_invoice_internal(
            input_path, 
            request.template_type, 
            request.options or InvoiceOptions(),
            request_id
        )
        
        # Clean up
        input_path.unlink()
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result["processing_time"] = processing_time
        
        return result
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "request_id": request_id,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                },
                "processing_time": processing_time
            }
        )

@app.post("/api/v1/invoice/generate/upload")
async def generate_invoice_upload(
    invoice_data: UploadFile = File(..., description="JSON file with invoice data"),
    template_type: Optional[str] = None,
    enable_daf: bool = False,
    enable_custom: bool = False
):
    """Generate invoice from uploaded JSON file"""
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    # Validate file type
    if not invoice_data.filename.endswith('.json'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JSON files are supported."
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as temp_file:
            content = await invoice_data.read()
            temp_file.write(content)
            input_path = Path(temp_file.name)
        
        # Create options
        options = InvoiceOptions(
            enable_daf=enable_daf,
            enable_custom=enable_custom
        )
        
        # Generate invoice
        result = await _generate_invoice_internal(input_path, template_type, options, request_id)
        
        # Clean up
        input_path.unlink()
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result["processing_time"] = processing_time
        
        return result
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "request_id": request_id,
                "error": {
                    "code": "PROCESSING_ERROR",
                    "message": str(e)
                },
                "processing_time": processing_time
            }
        )

@app.get("/api/v1/invoice/download/{request_id}")
async def download_invoice(request_id: str):
    """Download generated invoice by request ID (if implemented with storage)"""
    # This would require implementing a storage system for generated files
    # For now, return error indicating direct download from generate endpoints
    raise HTTPException(
        status_code=501,
        detail="Download by request ID not implemented. Use direct generation endpoints."
    )

# Internal helper functions

async def _generate_invoice_internal(
    input_path: Path, 
    template_type: Optional[str], 
    options: InvoiceOptions,
    request_id: str
) -> Dict[str, Any]:
    """Internal invoice generation logic"""
    
    # Create configuration
    config = InvoiceConfig(
        template_dir=Path("src/invoice_generator/TEMPLATE"),
        config_dir=Path("src/invoice_generator/config"),
        enable_daf=options.enable_daf,
        enable_custom=options.enable_custom,
        verbose=options.verbose
    )
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_output:
        output_path = Path(temp_output.name)
    
    try:
        # Generate invoice
        generator = InvoiceGenerator(config)
        result = generator.generate(input_path, output_path)
        
        if not result.success:
            return {
                "success": False,
                "request_id": request_id,
                "error": {
                    "code": "GENERATION_FAILED",
                    "message": result.error
                },
                "processing_time": result.duration
            }
        
        # Read generated file
        with open(output_path, 'rb') as f:
            file_data = f.read()
        
        # Encode as base64
        file_b64 = base64.b64encode(file_data).decode('utf-8')
        
        # Determine filename
        original_name = input_path.stem
        filename = f"{original_name}_generated.xlsx"
        
        response = {
            "success": True,
            "request_id": request_id,
            "result": {
                "file_data": file_b64,
                "filename": filename,
                "file_size": len(file_data),
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            },
            "metadata": {
                "template_type": template_type,
                "processing_duration": result.duration,
                "generated_at": datetime.now().isoformat()
            },
            "warnings": result.warnings
        }
        
        return response
        
    finally:
        # Clean up
        if output_path.exists():
            output_path.unlink()

# Alternative: Stream response for large files
@app.post("/api/v1/invoice/generate/stream")
async def generate_invoice_stream(request: InvoiceRequest):
    """Generate and stream invoice file directly"""
    # Implementation for streaming large files
    # Useful for very large Excel files
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)