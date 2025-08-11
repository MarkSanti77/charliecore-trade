from fastapi import HTTPException

@router.patch("/{call_id}/fechar", response_model=schemas.Call)
def fechar_call(call_id: int, exit_price: float, db: Session = Depends(get_db)):
    call = crud.fechar_call(db, call_id, exit_price)
    if not call:
        raise HTTPException(status_code=404, detail="Call não encontrada")
    return call
