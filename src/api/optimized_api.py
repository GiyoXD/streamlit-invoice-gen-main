#!/usr/bin/env python3
"""
Invoice Generator API - Optimized with Raw Binary Response
Much more efficient - send Excel files directly as binary data
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import tempfile
import uuid
from pathlib import Path
from datetime import datetime
import io

app = FastAPI(
    title="Invoice Generator API - Optimized",
    description="Generate Excel invoices - returns raw Excel files",
    version="2.0.0"
)

class InvoiceRequest(BaseModel):
    """JSON payload request model"""
    invoice_data: Dict[str, Any]
    template_type: Optional[str] = None
    enable_daf: bool = False
    enable_custom: bool = False

@app.post("/api/v1/invoice/generate")
async def generate_invoice_raw(request: InvoiceRequest):
    """Generate invoice and return raw Excel file"""
    
    # Create temp files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_input:
        json.dump(request.invoice_data, temp_input)
        input_path = Path(temp_input.name)
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_output:
        output_path = Path(temp_output.name)
    
    try:
        # Import and use existing generator
        from src.invoice_generator import generate_invoice
        
        result = generate_invoice(
            json_file_path=str(input_path),
            output_file_path=str(output_path),
            template_dir="src/invoice_generator/TEMPLATE",
            config_dir="src/invoice_generator/config",
            verbose=False
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=f"Generation failed: {result.get('error')}")
        
        # Determine filename
        original_name = request.invoice_data.get('metadata', {}).get('workbook_filename', 'invoice.xlsx')
        filename = f"generated_{original_name}"
        
        # Return raw Excel file
        return FileResponse(
            path=output_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Generation-Success": "true",
                "X-Processing-Time": str(result.get('duration', 0))
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup happens automatically with FileResponse
        input_path.unlink(missing_ok=True)

@app.post("/api/v1/invoice/generate/upload")
async def generate_invoice_upload_raw(
    invoice_data: UploadFile = File(...),
    template_type: Optional[str] = None
):
    """Upload JSON file and get raw Excel file back"""
    
    # Save uploaded file
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as temp_input:
        content = await invoice_data.read()
        temp_input.write(content)
        input_path = Path(temp_input.name)
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_output:
        output_path = Path(temp_output.name)
    
    try:
        # Import and use existing generator
        from src.invoice_generator import generate_invoice
        
        result = generate_invoice(
            json_file_path=str(input_path),
            output_file_path=str(output_path),
            template_dir="src/invoice_generator/TEMPLATE",
            config_dir="src/invoice_generator/config",
            verbose=False
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=f"Generation failed: {result.get('error')}")
        
        # Use original filename as base
        base_name = Path(invoice_data.filename).stem
        filename = f"{base_name}_generated.xlsx"
        
        # Return raw Excel file
        return FileResponse(
            path=output_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    finally:
        input_path.unlink(missing_ok=True)

@app.post("/api/v1/invoice/generate/stream")
async def generate_invoice_stream(request: InvoiceRequest):
    """Generate and stream Excel file for very large files"""
    
    # For large files, stream the response
    def generate():
        # Create temp files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as temp_input:
            json.dump(request.invoice_data, temp_input)
            temp_input.flush()
            
            with tempfile.NamedTemporaryFile(suffix='.xlsx') as temp_output:
                # Generate invoice
                from src.invoice_generator import generate_invoice
                
                result = generate_invoice(
                    json_file_path=temp_input.name,
                    output_file_path=temp_output.name,
                    template_dir="src/invoice_generator/TEMPLATE",
                    config_dir="src/invoice_generator/config",
                    verbose=False
                )
                
                if result.get('success'):
                    # Stream file in chunks
                    with open(temp_output.name, 'rb') as f:
                        while chunk := f.read(8192):  # 8KB chunks
                            yield chunk
                else:
                    raise HTTPException(status_code=500, detail="Generation failed")
    
    filename = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        generate(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)