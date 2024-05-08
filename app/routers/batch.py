# coding=utf-8

from fastapi import APIRouter, Depends, Header
from typing import List, Union

from app import models, schemas
from app.routers.product import adjust_inventory
from app.services import (
    batch_service,
    process_service,
    product_service,
    operation_service,
    batch_process_service,
)
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import HTTPException
from collections import defaultdict
import pandas as pd
import io

from app.dependencies import get_db

from datetime import datetime, timedelta
from enum import Enum

from app.services.day_invoice_service import remove_day_invoices_by_batch_id

router = APIRouter(
    prefix="/batch",
    tags=["batch"],
    responses={404: {"description": "Not found"}},
)


class BatchStatus(str, Enum):
    unstarted = "unstarted"
    ongoing = "ongoing"
    urgent = "urgent"
    finished = "finished"
    shipped = "shipped"
    cancelled = "cancelled"


@router.get("/", response_model=List[schemas.Batch])
def read_batches(db: Session = Depends(get_db)):
    batches = batch_service.get_batches(db=db)
    return batches


@router.get("/meta_info", response_model=List[schemas.Batch])
def read_batches_meta_info(db: Session = Depends(get_db)):
    batches = batch_service.get_batches_meta_info(db=db)
    return batches


@router.get("/unfinished", response_model=List[schemas.Batch])
def read_unfinished_batches(db: Session = Depends(get_db)):
    ongoing_batches = batch_service.get_batches_by_status("ongoing", db=db)
    urgent_batches = batch_service.get_batches_by_status("urgent", db=db)
    unstarted_batches = batch_service.get_batches_by_status("unstarted", db=db)
    total_display = ongoing_batches + urgent_batches + unstarted_batches
    return total_display if len(total_display) > 0 else []


@router.get("/working", response_model=List[schemas.Batch])
def read_working_batches(db: Session = Depends(get_db)):
    ongoing_batches = batch_service.get_batches_by_status("ongoing", db=db)
    urgent_batches = batch_service.get_batches_by_status("urgent", db=db)
    return ongoing_batches + urgent_batches


@router.get("/collected", response_model=List[schemas.Batch])
def read_collected_batches(db: Session = Depends(get_db)):
    finished_batches = batch_service.get_batches_by_status("finished", db=db)
    shipped_batches = batch_service.get_batches_by_status("shipped", db=db)
    return finished_batches + shipped_batches


@router.get("/recent", response_model=List[schemas.Batch])
def read_recent_ended_batches(db: Session = Depends(get_db)):
    tod = datetime.now()
    week = timedelta(days=7)
    target = tod - week
    return batch_service.get_batches_end_after(target, db=db)


@router.get("/{batch_id}", response_model=schemas.Batch)
def read_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = batch_service.get_batch(batch_id=batch_id, db=db)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.get("/meta_info/{batch_id}", response_model=schemas.Batch)
def read_batch_meta_info(batch_id: int, db: Session = Depends(get_db)):
    batch = batch_service.get_batch(batch_id=batch_id, db=db)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.get("/product_id/{product_id}/{status}")
def read_batches_by_product_id_and_status(
    product_id: str, status: BatchStatus, db: Session = Depends(get_db)
):
    if not status:
        batches = batch_service.get_batches_by_product_id(product_id=product_id, db=db)
    else:
        batches = batch_service.get_batches_by_product_id_and_status(
            product_id=product_id, status=status.value, db=db
        )
    if not batches:
        raise HTTPException(status_code=404, detail="No batch found")
    return batches


@router.get("/status/{status}", response_model=List[schemas.Batch])
def read_batch_by_status(status: BatchStatus, db: Session = Depends(get_db)):
    batch = batch_service.get_batches_by_status(status=status, db=db)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.get("/plan_amount_over/{amount}")
def read_batch_plan_amount_over(amount: int, db: Session = Depends(get_db)):
    return batch_service.get_batches_plan_amount_over(amount=amount, db=db)


@router.get("/plan_amount_equal/{amount}")
def read_batch_plan_amount_equal(amount: int, db: Session = Depends(get_db)):
    return batch_service.get_batches_plan_amount_equal(amount=amount, db=db)


@router.get("/plan_amount_under/{amount}")
def read_batch_plan_amount_under(amount: int, db: Session = Depends(get_db)):
    return batch_service.get_batches_plan_amount_under(amount=amount, db=db)


@router.get("/not_fulfilled")
def read_batch_not_fulfilled(db: Session = Depends(get_db)):
    return batch_service.get_batches_not_fulfilled(db=db)


@router.get("/start_after/{date}")
def read_batch_start_after(date: datetime, db: Session = Depends(get_db)):
    return batch_service.get_batches_start_after(date=date, db=db)


@router.get("/start_on/{date}")
def read_batch_start_on(date: datetime, db: Session = Depends(get_db)):
    return batch_service.get_batches_start_on(date=date, db=db)


@router.get("/start_before/{date}")
def read_batch_start_before(date: datetime, db: Session = Depends(get_db)):
    return batch_service.get_batches_start_before(date=date, db=db)


@router.get("/batch-summary/download/{batch_id}.csv")
async def download_batch_summary_csv(batch_id: int, db: Session = Depends(get_db)):
    db_batch = batch_service.get_batch(batch_id=batch_id, db=db)
    columns = [
        "排产",
        "达产",
        "交付率",
        "总计配件成本（标准）",
        "总计配件成本（实际）",
        "总计人力成本（标准）",
        "总计人力成本（实际）",
        "单位配件成本（标准）",
        "单位配件成本（实际）",
        "单位人力成本（标准）",
        "单位人力成本（实际）",
    ]
    records = {}
    b_spec_ta, b_spec_ti, b_emp_ta, b_emp_ti = 0, 0, 0, 0
    b_spec_ua, b_spec_ui, b_emp_ua, b_emp_ui = 0, 0, 0, 0
    consumption, ideal_unit_consumption = defaultdict(int), defaultdict(int)
    for bp in db_batch.batch_process:
        bp_spec_ta, bp_spec_ti, bp_emp_ta, bp_emp_ti = 0, 0, 0, 0
        bp_spec_ua, bp_spec_ui, bp_emp_ua, bp_emp_ui = 0, 0, 0, 0
        # 标准消耗量是batch层面的数据，计划略复杂，不能以work数据算
        # （某道工艺未100%达产会导致后面的 work plan 都不是标准用量）
        # 所以用 warehouse record 去计算单位产品的标准用量，最后乘 batch plan
        for wr in bp.warehouse_record:
            ideal_unit_consumption[wr.component_name] += wr.consumption
            # 记录【bp 标准单位】
            bp_spec_ui += wr.specification_gross_price * wr.consumption
        for w in bp.work:
            w_spec_ta, w_spec_ti, w_emp_ta, w_emp_ti = 0, 0, 0, 0
            w_spec_ua, w_spec_ui, w_emp_ua, w_emp_ui = 0, 0, 0, 0
            # 配件成本 = 配件价格 * （标准|实际用量）
            # 逐个配件来加总
            for ws in w.work_specification:
                w_spec_ta += ws.specification_gross_price * ws.actual_amount
                w_spec_ti += ws.specification_gross_price * ws.plan_amount
                # 同时记录实际消耗量
                consumption[ws.component_name] += ws.actual_amount
            # 人力成本
            w_emp_ta = w.complete_hour * w.hour_pay + w.complete_unit * w.unit_pay
            w_emp_ti = bp.unit_pay * w.plan_unit
            w_emp_ua = w_emp_ta / (w.complete_unit or w.plan_unit)
            w_emp_ui = bp.unit_pay
            w_spec_ua = w_spec_ta / (w.complete_unit or w.plan_unit)
            w_spec_ui = w_spec_ui / w.plan_unit
            # 将 work 数据处理进 【bp 实际总】
            bp_spec_ta += w_spec_ta
            bp_emp_ta += w_emp_ta
        # 【bp 标准总】 需要 【bp 开始数量】
        # 【bp 实际单位】 需要 【bp 结束数量】
        bp_spec_ti = bp_spec_ui * bp.start_amount
        bp_spec_ua = bp_spec_ta / bp.end_amount
        bp_emp_ti = bp.start_amount * bp.unit_pay
        bp_emp_ua = bp_emp_ta / bp.end_amount
        bp_emp_ui = bp.unit_pay
        # 记录本条 bp
        bp_record_index = (
            str(bp.process.process_order) + " - " + bp.process.process_name
        )
        records[bp_record_index] = [
            bp.start_amount,
            bp.end_amount,
            bp.end_amount / bp.start_amount,
            bp_spec_ti,
            bp_spec_ta,
            bp_emp_ti,
            bp_emp_ta,
            bp_spec_ui,
            bp_spec_ua,
            bp_emp_ui,
            bp_emp_ua,
        ]
        # 将 bp 数据处理进 【batch 实际总】
        b_spec_ta += bp_spec_ta
        b_spec_ti += bp_spec_ti
        b_emp_ta += bp_emp_ta
        b_emp_ti += bp_emp_ti

    # 计算【bp 单位】
    b_spec_ua = b_spec_ta / db_batch.actual_amount
    b_spec_ui = b_spec_ti / db_batch.plan_amount
    b_emp_ua = b_emp_ta / db_batch.actual_amount
    b_emp_ui = b_emp_ti / db_batch.plan_amount
    # 记录本条 batch
    batch_record_index = "批次" + str(batch_id) + "总计"
    records[batch_record_index] = [
        db_batch.plan_amount,
        db_batch.actual_amount,
        db_batch.actual_amount / db_batch.plan_amount,
        b_spec_ti,
        b_spec_ta,
        b_emp_ti,
        b_emp_ta,
        b_spec_ui,
        b_spec_ua,
        b_emp_ui,
        b_emp_ua,
    ]

    df = pd.DataFrame.from_dict(records, orient="index", columns=columns).reset_index()
    response = StreamingResponse(
        io.StringIO("\ufeff" + df.to_csv(index=False, ncoding="utf-8-sig")),
        media_type="text/csv",
    )
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename={str(db_batch.id)}.csv"
    return response


@router.post("/")
def create_batch(
    batch: schemas.BatchCreate,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    month_db_existing = batch_service.get_batches_in_month(
        batch.start.year, batch.start.month, db=db
    )
    prefix = ((batch.start.year - 2000) * 100 + batch.start.month) * 100
    suffix = 1 if not month_db_existing else (1 + len(month_db_existing))
    batch.id = prefix + suffix
    batch_dict = batch.dict()
    batch_dict.pop("product_name", None)
    new_batch = models.Batch(**batch_dict)
    processes = sorted(
        process_service.get_processes_by_product_id(product_id=batch.product_id, db=db),
        key=lambda x: x.process_order,
    )
    for process in processes:
        # create_batch_process(batch_process: schemas.BatchProcessCreate, db: Session)
        # {unit_pay: p.unit_pay, batch_id: Number(batch.id), process_id: String(p.id), status: 'unstarted'};
        bp_info = schemas.BatchProcessCreate(
            status="unstarted",
            process_id=process.id,
            batch_id=new_batch.id,
            unit_pay=process.unit_pay,
        )
        # new_bp = batch_process_service.create_batch_process(batch_process=bp_info, db=db)
        new_bp = models.BatchProcess(**bp_info.dict())
        new_batch.batch_process.append(new_bp)
    db.add(new_batch)
    db.flush()
    db.refresh(new_batch)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"创建生产批次 {new_batch.product_id} * {new_batch.plan_amount} @ {new_batch.start}",
        db,
    )
    print(f"[!] Created new batch for product: {new_batch.product_id}")
    return new_batch


@router.put("/")
def update_batch(
    batch: schemas.Batch,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    db_batch_data = batch_service.get_batch(batch.id, db=db)
    if not db_batch_data:
        raise HTTPException(status_code=400, detail="Matching batch not found")
    db_batch_model = schemas.Batch(**jsonable_encoder(db_batch_data))
    update_data = batch.dict(exclude_unset=True)
    updated_batch = batch_service.update_batch(
        batch=db_batch_model.copy(update=update_data), db=db
    )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"更新生产批次 {updated_batch.product_id} * {updated_batch.plan_amount} @ {updated_batch.start}",
        db,
    )
    # remove day invoices inside
    if batch.status == "cancelled":
        remove_day_invoices_by_batch_id(batch_id=batch.id, db=db)
    return updated_batch


@router.put("/auto_update_status")
def auto_update_status(db: Session = Depends(get_db)):
    current = datetime.now()
    unstarted_batches = batch_service.get_batches_by_status("unstarted", db=db)
    for b in unstarted_batches:
        if b.start <= current:
            b.status = "ongoing"
            batch_service.update_batch(b, db=db)
    return JSONResponse(content={"success": True})


@router.put("/complete/{batch_id}/{actual_amount}")
def complete_batch(
    batch_id: int,
    actual_amount: int,
    update_inventory: bool = True,
    authorization: Union[str, None] = Header(default=None),
    db: Session = Depends(get_db),
):
    target_batch = batch_service.get_batch(batch_id, db=db)
    target_batch.status = "finished"
    target_batch.actual_amount = actual_amount
    target_batch.end = datetime.now()
    completed_batch = batch_service.update_batch(batch=target_batch, db=db)
    # update product inventory
    if update_inventory:
        updated_product = adjust_inventory(
            product_id=completed_batch.product_id,
            adjust_number=actual_amount,
            authorization=authorization,
            db=db,
        )
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"标记生产批次为[完成] {completed_batch.product_id} * {completed_batch.plan_amount} @ {completed_batch.start}",
        db,
    )
    return completed_batch


@router.delete("/{batch_id}")
def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    db_batch_data = batch_service.get_batch(batch_id, db=db)
    if not db_batch_data:
        raise HTTPException(status_code=400, detail="Matching batch not found")
    batch_service.delete_batch(batch=db_batch_data, db=db)
    return JSONResponse(content={"success": True})
