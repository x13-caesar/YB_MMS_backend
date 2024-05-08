# coding=utf-8
import os.path
from datetime import datetime, date
from typing import List, Union
from urllib.parse import quote

import pandas as pd
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from openpyxl import Workbook
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import schemas, models
from app.dependencies import get_db
from app.excel_content import generate_formatted_instock_form, wipe_old_files
from app.routers import specification
from app.routers.specification import (
    get_component_by_specification_id,
    read_specification, check_if_spec_use_net_price,
)
from app.services import operation_service
from app.services.operation_service import extract_user_from_authentication

router = APIRouter(
    prefix="/instock",
    tags=["instock"],
    responses={404: {"description": "Not found"}},
)


@router.get("/form", response_model=List[schemas.InstockForm])
def read_instock_forms(
        form_id: int = None,
        form_status: str = None,
        paid: bool = None,
        db: Session = Depends(get_db),
):
    criteria = dict()
    if form_id is not None:
        criteria["form_id"] = form_id
    if form_status is not None:
        criteria["form_status"] = form_status
    if paid is not None:
        criteria["paid"] = paid
    return db.query(models.InstockForm).filter_by(**criteria).all()


@router.get("/historical-form", response_model=List[schemas.InstockForm])
def read_historical_instock_forms(db: Session = Depends(get_db)):
    return (
        db.query(models.InstockForm)
            .filter(models.InstockForm.form_status != "ongoing")
            .all()
    )


@router.post("/form")
def create_new_instock_form(
        form: schemas.InstockFormCreate,
        authorization: Union[str, None] = Header(default=None),
        db: Session = Depends(get_db),
):
    # 创建时间的缺省值为后台处理时间
    if not form.create_time:
        form.create_time = datetime.now()
    # generate id for the form
    year_begin = datetime(form.create_time.year, 1, 1)
    existing_form_of_curr_year = db.query(models.InstockForm.display_form_id) \
        .filter(models.InstockForm.create_time >= year_begin, models.InstockForm.vendor_id == form.vendor_id) \
        .all()
    print(existing_form_of_curr_year)
    if len(existing_form_of_curr_year) == 0:
        new_count = 1
    else:
        new_count = max([int(oid[0][-4:]) for oid in existing_form_of_curr_year]) + 1
    new_display_id = f"{form.create_time.strftime('%Y%m%d')}-{str(form.vendor_id).rjust(3, '0')}-{str(new_count).rjust(4, '0')}"
    # for new form object
    form_info_dict = form.dict()
    form_info_dict['display_form_id'] = new_display_id
    items = form_info_dict.pop("instock_item", None)
    # 写入 instock_form
    new_form_obj = models.InstockForm(**form_info_dict)
    db.add(new_form_obj)
    db.flush()
    db.refresh(new_form_obj)

    # 写入 instock_item
    if items:
        for item in items:
            spec = read_specification(specification_id=item["specification_id"], db=db)
            item["form_id"] = new_form_obj.form_id
            item["last_time"] = item["last_time"][:10]
            item["notice"] = spec.notice
            for attr in ["name", "model", "as_unit", "unit_amount", "vendor_id"]:
                item.pop(attr, None)
            new_item = models.InstockItem(**item)
            db.add(new_item)
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"创建新采购单 {new_form_obj.form_id}（供应商: {new_form_obj.vendor.company}）",
        db,
    )
    created_form = db.query(models.InstockForm).filter(models.InstockForm.form_id == new_form_obj.form_id).first()
    response = created_form.__dict__.copy()
    response.pop('_sa_instance_state', None)
    return response


@router.post("/multiple-form")
def create_multiple_new_forms(
        forms: List[schemas.InstockFormCreate],
        authorization: Union[str, None] = Header(default=None),
        db: Session = Depends(get_db),
):
    created_forms = []
    for form in forms:
        new_form_data = create_new_instock_form(form, authorization, db)
        new_form_id = new_form_data.get('form_id', None)
        new_form = db.query(models.InstockForm).filter(models.InstockForm.form_id == new_form_id).first()
        created_forms.append(new_form.__dict__.copy())
    return created_forms


@router.get("/ongoing-item")
def get_instock_items(db: Session = Depends(get_db)):
    ongoing_forms = db.query(models.InstockForm).filter(
        models.InstockForm.form_status == 'ongoing').all()
    response = []
    for f in ongoing_forms:
        for item in f.instock_item:
            if item.warehouse_quantity < item.order_quantity:
                item.display_form_id = f.display_form_id
                item_obj = item.__dict__
                item_obj = enrich_instock_item(item_obj, f, db=db)
                response.append(item_obj)
    return response


def enrich_instock_item(instock_item, instock_form=None, db: Session = Depends(get_db)):
    # cast instock item
    if isinstance(instock_item, models.InstockItem):
        instock_item = instock_item.__dict__
    elif isinstance(instock_item, schemas.InstockItem):
        instock_item = instock_item.dict()
    # get corresponding form if not given
    if not instock_form:
        instock_form = db.query(models.InstockForm).filter(
            models.InstockForm.form_id == instock_item['form_id']).first()
    # do enriching
    compo = db.query(models.Specification).filter(
        models.Specification.id == instock_item["specification_id"]).first().component
    display = {
        "form_id": instock_form.display_form_id,
        "company": instock_form.vendor.company,
        "create_time": instock_form.create_time,
        "component_name": compo.name,
        "model": compo.model,
        "as_unit": compo.as_unit
    }
    instock_item['display'] = display
    return instock_item


@router.get("/enriched_item")
def get_enriched_item(form_id: int = None, instock_item_id: int = None, db: Session = Depends(get_db)):
    if form_id is not None:
        items = db.query(models.InstockItem).filter(models.InstockItem.form_id == form_id).all()
        print(items)
    else:
        items = db.query(models.InstockItem).filter(models.InstockItem.instock_item_id == instock_item_id).all()
    response = []
    for item in items:
        response.append(enrich_instock_item(instock_item=item, instock_form=item.instock_form, db=db))
    print(response)
    return response


@router.post("/item")
def create_new_instock_item(
        item: schemas.InstockItem,
        authorization: Union[str, None] = Header(default=None),
        db: Session = Depends(get_db),
):
    # 创建时间的缺省值为后台处理时间
    if not item.last_time:
        item.last_time = datetime.now()
    new_item = models.InstockItem(**item.dict())
    db.add(new_item)
    db.flush()
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"向采购单 {new_item.form_id} 添加新配件 {new_item.specification_id} * {new_item.order_quantity}",
        db,
    )
    db.refresh(new_item)
    return new_item


@router.put("/form")
def update_instock_form(
        form: schemas.InstockForm,
        authorization: Union[str, None] = Header(default=None),
        db: Session = Depends(get_db),
):
    update_content = form.dict()
    # drop unneeded fields
    useless_attributes = ["vendor", "instock_item", "display_form_id", "display_vendor_id"]
    for attr in useless_attributes:
        update_content.pop(attr, None)
    # remove other keys to avoid collisions
    # update_content.pop("vendor_id", None)
    # update
    print(update_content)
    db.query(models.InstockForm).filter(
        models.InstockForm.form_id == form.form_id, models.InstockForm.vendor_id == form.vendor_id
    ).update(update_content)
    db.commit()
    # logging
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"更新采购单 {form.form_id}",
        db,
    )
    return (
        db.query(models.InstockForm)
            .filter(models.InstockForm.form_id == form.form_id)
            .first()
    )


@router.put("/multiple-form")
def update_multiple_instock_forms(
        forms: List[schemas.InstockForm],
        authorization: Union[str, None] = Header(default=None),
        db: Session = Depends(get_db),
):
    response = []
    for form in forms:
        updated_form = update_instock_form(form, authorization, db)
        response.append(updated_form)
    return response


@router.put("/change-form-paid")
def change_form_paid(form_id: int, paid: bool, authorization: Union[str, None] = Header(default=None),
                     db: Session = Depends(get_db)):
    db.query(models.InstockForm).filter(models.InstockForm.form_id == form_id).update({"paid": paid})
    # log operation
    operation_service.log_operation_with_authentication_token(
        authorization, f"修改采购单 {form_id} 状态为 {'已支付' if paid else '未支付'}", db
    )
    return {"success": True}


@router.put("/item")
def update_instock_item(
        item: schemas.InstockItem,
        authorization: Union[str, None] = Header(default=None),
        db: Session = Depends(get_db),
):
    prev_item = (
        db.query(models.InstockItem)
            .filter(models.InstockItem.instock_item_id == item.instock_item_id)
            .first()
    )
    stock_increase = item.warehouse_quantity - prev_item.warehouse_quantity
    # 如果有新入库，增加库存
    specification.adjust_stock(
        spec_id=item.specification_id,
        adjust_number=stock_increase,
        authorization=authorization,
        db=db,
    )
    # update
    update_contents = item.dict()
    update_contents.pop('display', None)
    db.query(models.InstockItem).filter(
        models.InstockItem.instock_item_id == item.instock_item_id
    ).update(update_contents)
    db.commit()
    # logging
    operation_service.log_operation_with_authentication_token(
        authorization,
        f"更新采购单 {item.form_id} 的项目 {item.instock_item_id}",
        db,
    )
    updated_instock_item = (
        db.query(models.InstockItem)
            .filter(models.InstockItem.instock_item_id == item.instock_item_id)
            .first()
    )
    return enrich_instock_item(instock_item=updated_instock_item, db=db)


class NewInstockEvent(BaseModel):
    instock_item_id: int
    new_instock_amount: int


@router.put("/new-instock-event")
def new_instock_event(
        new_instock_event: NewInstockEvent,
        authorization: Union[str, None] = Header(default=None),
        db: Session = Depends(get_db),
):
    parent_item_filter = db.query(models.InstockItem).filter(
        models.InstockItem.instock_item_id == new_instock_event.instock_item_id
    )
    parent_item = parent_item_filter.first()
    new_balance = parent_item.warehouse_quantity + new_instock_event.new_instock_amount
    instock_time = datetime.now()
    # new record
    dict_record = {
        "instock_item_id": new_instock_event.instock_item_id,
        "amount_in": new_instock_event.new_instock_amount,
        "balance": new_balance,
        "operator": extract_user_from_authentication(authorization),
        "record_time": instock_time,
    }
    record = models.InstockRecord(**dict_record)
    db.add(record)
    # update instock_item
    parent_item_filter.update(
        {"warehouse_quantity": new_balance, "last_time": instock_time}
    )
    db.commit()
    return parent_item_filter.first()


@router.put("/multiple-item")
def update_multiple_instock_items(
        items: List[schemas.InstockItem],
        authorization: Union[str, None] = Header(default=None),
        db: Session = Depends(get_db),
):
    response = []
    for item in items:
        updated_item = update_instock_item(item, authorization, db)
        response.append(updated_item)
    return response


@router.get("/record", response_model=List[schemas.InstockRecord])
def get_instock_record(
        instock_item_id: int = None,
        instock_form_id: int = None,
        db: Session = Depends(get_db),
):
    if instock_form_id:
        query_result = (
            db.query(models.InstockItem.instock_item_id)
                .filter(models.InstockItem.form_id == instock_form_id)
                .all()
        )
        instock_item_id_list = [x for (x,) in query_result]
    else:
        instock_item_id_list = [instock_item_id]
    records = (
        db.query(models.InstockRecord)
            .filter(models.InstockRecord.instock_item_id.in_(instock_item_id_list))
            .all()
    )
    return records


def enrich_instock_record(instock_record: Union[models.InstockRecord, schemas.InstockRecord],
                          db: Session = Depends(get_db)):
    if isinstance(instock_record, models.InstockRecord):
        instock_record = instock_record.__dict__
    elif isinstance(instock_record, schemas.InstockRecord):
        instock_record = instock_record.dict()
    instock_item = db.query(models.InstockItem).filter(
        models.InstockItem.instock_item_id == instock_record['instock_item_id']).first()
    enriched_item = enrich_instock_item(instock_item=instock_item, instock_form=instock_item.instock_form, db=db)
    # do enriching
    if not enriched_item["unit_cost"]:
        enriched_item["unit_cost"] = 0
    display = {
        "company": enriched_item["display"]["company"],
        "specification_id": enriched_item["specification_id"],
        "component_name": enriched_item["display"]["component_name"],
        "model": enriched_item["display"]["model"],
        "form_id": enriched_item["display"]["form_id"],
        "total_value": enriched_item["unit_cost"] * instock_record["amount_in"],
        "notice": enriched_item["notice"],
        "paid": enriched_item["instock_form"].paid,
        "use_net": check_if_spec_use_net_price(spec_id=enriched_item['specification_id'], db=db)['use_net'],
    }
    instock_record['display'] = display
    return instock_record


@router.get("/records-in-date-range", response_model=List[schemas.InstockRecord])
def get_instock_record_in_time_range(
        start: date = None,
        end: date = None,
        db: Session = Depends(get_db),
):
    if not start or not end:
        print("Please specify the date range (start and end).")
        raise HTTPException(status_code=504, detail="No date range specified.")
    records = (
        db.query(models.InstockRecord)
            .filter(models.InstockRecord.record_time.between(start, end))
            .all()
    )
    response = []
    for r in records:
        response.append(enrich_instock_record(instock_record=r, db=db))
    return response


@router.get('/instock-record-in-excel')
async def download_instock_record_excel(
        start: date = None,
        end: date = None,
        db: Session = Depends(get_db),
):
    instock_records = get_instock_record_in_time_range(start, end, db)

    # clean up old files
    pwd = os.getcwd()
    wipe_old_files(pwd)

    filename = f"入库记录 {start.strftime('%Y-%m-%d')}-{end.strftime('%Y-%m-%d')}.xlsx"

    # data processing
    data = pd.json_normalize(instock_records, sep='.')
    data.drop(['_sa_instance_state'], axis=1, inplace=True)
    data['display.paid'].fillna("FALSE", inplace=True)
    data['display.use_net'].fillna("FALSE", inplace=True)
    # data.replace(["TRUE", "FALSE"], ["是", "否"], inplace=True)
    data.rename(
        columns={'id': '记录编号',
                 'instock_item_id': '采购内容序列号',
                 'display.company': '供应商',
                 'display.specification_id': '物料编号',
                 'display.component_name': '物料名称',
                 'display.model': '物料型号',
                 'amount_in': '本次入库数量',
                 'balance': '记录后总入库数量',
                 'record_time': '入库时间',
                 'display.form_id': '采购单编号',
                 'display.total_value': '入库价值金额',
                 'display.notice': '采购备注',
                 'display.paid': '是否付款',
                 'display.use_net': '使用税前价',
                 'operator': '操作员',
                 'note': '入库备注'
                 },
        inplace=True,
    )
    save_path = os.path.join(pwd, filename)
    data.to_excel(save_path)
    print("Saving worksheet to " + save_path)
    headers = {
        "Content-Disposition": "attachment; filename*=utf-8''{}".format(quote(filename))
    }
    return FileResponse(save_path, headers=headers)


@router.get("/form-as-preview")
def read_instock_form_in_preview_format(form_id: int, db: Session = Depends(get_db)):
    form = (
        db.query(models.InstockForm)
            .filter(models.InstockForm.form_id == form_id)
            .first()
    )
    response = form.__dict__
    print(response)
    items_in_preview = []
    for item in response["instock_item"]:
        item_as_preview = item.__dict__
        spec = read_specification(
            specification_id=item_as_preview["specification_id"], db=db
        )
        compo = get_component_by_specification_id(
            spec_id=item_as_preview["specification_id"], db=db
        )
        item_as_preview["name"] = compo.name  # 物料名称
        item_as_preview["model"] = compo.model  # 型号
        item_as_preview["as_unit"] = compo.as_unit  # 单位
        item_as_preview["unit_amount"] = spec.unit_amount  # 包装数量
        items_in_preview.append(item_as_preview)
    response.update({"instock_item": items_in_preview})
    return response


@router.get("/form-in-excel")
async def download_instock_form_excel(form_id: int, db: Session = Depends(get_db)):
    form = (
        db.query(models.InstockForm)
            .filter(models.InstockForm.form_id == form_id)
            .first()
    )

    # clean up old files
    pwd = os.getcwd()
    wipe_old_files(pwd)

    # create worksheet
    workbook = Workbook()
    sheet = workbook.active

    filename = generate_formatted_instock_form(sheet, form, db)

    save_path = os.path.join(pwd, filename)

    print("Saving worksheet to " + save_path)
    workbook.save(save_path)

    headers = {
        "Content-Disposition": "attachment; filename*=utf-8''{}".format(quote(filename))
    }
    return FileResponse(save_path, headers=headers)
