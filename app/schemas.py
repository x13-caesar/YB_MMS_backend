# coding=utf-8
from datetime import datetime, date
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class VendorBase(BaseModel):
    name: str
    company: str
    payment_period: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    fax: Optional[str] = None
    notice: Optional[str] = None


class VendorCreate(VendorBase):
    pass


class Vendor(VendorBase):
    id: str
    display_id: str

    class Config:
        orm_mode = True


class ComponentBase(BaseModel):
    id: str
    name: str
    category: str
    model: Optional[str]
    description: Optional[str]
    expiration: Optional[str]
    as_unit: Optional[str] = None
    unit_weight: Optional[str]
    warn_stock: int
    picture: Optional[str]
    notice: Optional[str]
    fill_period: Optional[str]
    hide: bool = False


class ComponentCreate(ComponentBase):
    pass


class SpecificationBase(BaseModel):
    id: Optional[str]
    component_id: str
    vendor_id: Optional[int]
    gross_price: Optional[float]
    net_price: Optional[float]
    use_net: Optional[bool] = True
    stock: int = 0
    unit_amount: Optional[int]
    blueprint: Optional[str]
    notice: Optional[str]
    hide: bool = False


class SpecificationCreate(SpecificationBase):
    pass


class Specification(SpecificationBase):
    vendor: Optional[Vendor]
    component_name: Optional[str]
    display_vendor_id: Optional[str]

    class Config:
        orm_mode = True


class Component(ComponentBase):
    specification: Optional[List[Specification]]

    class Config:
        orm_mode = True


class CompoCategoryBase(BaseModel):
    category: str
    prefix: str


class CompoCategoryCreate(CompoCategoryBase):
    pass


class CompoCategory(CompoCategoryBase):
    id: int

    class Config:
        orm_mode = True


class BuyerBase(BaseModel):
    name: str
    company: str
    payment_period: Optional[str]
    contact: Optional[str]
    address: Optional[str]
    notice: Optional[str]


class BuyerCreate(BuyerBase):
    pass


class Buyer(BuyerBase):
    id: int

    class Config:
        orm_mode = True


class ProcessComponentBase(BaseModel):
    id: Optional[int]
    process_id: Optional[str]
    component_id: str
    attrition_rate: float = 0.001
    consumption: int = 1


class ProcessComponentCreate(ProcessComponentBase):
    pass


class ProcessComponent(ProcessComponentBase):
    component: Optional[Component]

    class Config:
        orm_mode = True


class ProcessBase(BaseModel):
    id: Optional[str]
    process_name: str
    product_id: Optional[str]
    process_order: int
    notice: Optional[str]
    unit_pay: float
    process_component: Optional[List[ProcessComponent]]


class ProcessCreate(ProcessBase):
    pass


class Process(ProcessBase):
    class Config:
        orm_mode = True


class ProductBase(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str]
    inventory: int
    picture: Optional[str]
    custom: Optional[str]
    notice: Optional[str]
    deprecated: bool = False
    deprecated_date: Optional[datetime]
    process: Optional[List[Process]]


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    class Config:
        orm_mode = True


class ProductCategoryBase(BaseModel):
    category: str


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategory(ProductCategoryBase):
    id: int

    class Config:
        orm_mode = True


class WarehouseRecordBase(BaseModel):
    batch_process_id: int
    component_id: str
    component_name: str
    specification_id: Optional[str]
    consumption: int = 1
    specification_net_price: Optional[float]
    specification_gross_price: Optional[float]


class WarehouseRecordCreate(WarehouseRecordBase):
    pass


class WarehouseRecord(WarehouseRecordBase):
    id: int

    class Config:
        orm_mode = True


class WorkSpecificationBase(BaseModel):
    work_id: int
    specification_id: str
    plan_amount: int
    actual_amount: int = 0
    component_name: str
    specification_net_price: Optional[float]
    specification_gross_price: Optional[float]


class WorkSpecificationCreate(WorkSpecificationBase):
    pass


class WorkSpecification(WorkSpecificationBase):
    id: int

    class Config:
        orm_mode = True


class WorkBase(BaseModel):
    batch_process_id: int
    employee_id: int
    employee_name: str
    work_date: datetime
    unit_pay: Optional[float]
    complete_unit: Optional[int]
    hour_pay: Optional[float]
    complete_hour: Optional[int]
    plan_unit: int
    check: bool
    salary_id: Optional[int] = None
    product_name: str
    process_name: str


class WorkCreate(WorkBase):
    pass


class Work(WorkBase):
    id: int
    work_specification: Optional[List[WorkSpecification]]

    class Config:
        orm_mode = True


class BatchProcessBase(BaseModel):
    status: str
    process_id: str
    batch_id: int
    start_amount: Optional[int]
    end_amount: Optional[int]
    unit_pay: float


class BatchProcessCreate(BatchProcessBase):
    pass


class BatchProcess(BatchProcessBase):
    id: int
    work: Optional[List[Union[Work, WorkCreate]]]
    process: Optional[Process]
    warehouse_record: Optional[List[WarehouseRecord]]

    class Config:
        orm_mode = True


class BatchBase(BaseModel):
    id: Optional[int]
    status: str
    product_id: str
    plan_amount: int
    actual_amount: Optional[int]
    create: datetime
    start: datetime
    end: Optional[datetime]
    ship: Optional[datetime]
    notice: Optional[str]


class BatchCreate(BatchBase):
    pass


class Batch(BatchBase):
    batch_process: Optional[List[BatchProcess]]
    product_name: Optional[str] = None

    class Config:
        orm_mode = True


class DeliveryBase(BaseModel):
    product_id: str
    amount: int
    order_id: Optional[str]
    buyer_id: int
    deliver_date: date
    unit_price: float
    total_price: float
    reconciled: bool = False
    paid: bool = False
    notice: Optional[str]


class DeliveryCreate(DeliveryBase):
    pass


class Delivery(DeliveryBase):
    id: int
    buyer: Optional[Buyer]
    product_name: Optional[str] = None

    class Config:
        orm_mode = True


class OperationBase(BaseModel):
    content: str
    operator: str
    execute_time: datetime


class OperationCreate(OperationBase):
    pass


class Operation(OperationBase):
    id: int

    class Config:
        orm_mode = True


class EmployeeBase(BaseModel):
    name: str
    gender: Optional[str]
    birth: Optional[date] = None
    phone: Optional[str] = None
    ssn: Optional[str] = None
    department: Optional[str] = None
    status: str
    onboard: Union[date, str] = None
    notice: Optional[str] = None
    last_pay_check: Optional[datetime] = None


class EmployeeCreate(EmployeeBase):
    pass


class Employee(EmployeeBase):
    id: int

    class Config:
        orm_mode = True


class DayInvoiceBase(BaseModel):
    batch_id: int
    process_name: str
    employee_id: int
    employee_name: Optional[str]
    work_date: datetime
    unit_pay: Optional[float]
    complete_unit: Optional[int]
    hour_pay: Optional[float]
    complete_hour: Optional[int]
    check_status: bool = False
    check_date: Optional[datetime] = None


class DayInvoiceCreate(DayInvoiceBase):
    pass


class DayInvoice(DayInvoiceBase):
    id: int
    salary_id: Optional[int]

    class Config:
        orm_mode = True


class SalaryBase(BaseModel):
    employee_id: int
    employee_name: str
    start_date: date
    end_date: date
    unit_salary: Optional[float]
    hour_salary: Optional[float]
    deduction: float = 0
    bonus: float = 0
    status: str
    notice: Optional[str]
    check_date: Optional[datetime]


class SalaryCreate(SalaryBase):
    pass


class Salary(SalaryBase):
    id: int
    work: Optional[List[Work]]
    # day_invoice: Optional[List[DayInvoice]]

    class Config:
        orm_mode = True


class InstockItem(BaseModel):
    instock_item_id: Optional[int]
    form_id: Optional[int]
    specification_id: str
    order_quantity: int  # 订购数量
    unit_cost: Optional[float]
    warehouse_quantity: int  # 实际入库数量
    last_time: Optional[datetime]  # 最后一次更新
    instock_date: date  # 预计到货日期
    vendor_instock_date: date = None  # 供应商回复交期
    notice: Optional[str]
    # for display only
    # - company
    # - create_time
    # - component_name
    # - model
    # - as_unit
    display: dict = None
    display_form_id: str = None

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class InstockFormBase(BaseModel):
    vendor_id: int
    create_time: Optional[datetime]
    form_status: str
    note: Optional[str]
    amount: Optional[float]
    paid: Optional[bool]
    instock_item: Optional[List]


class InstockFormCreate(InstockFormBase):
    pass


class InstockForm(InstockFormBase):
    form_id: int
    display_form_id: str
    vendor: Optional[Vendor]
    display_vendor_id: Optional[str]

    class Config:
        orm_mode = True


class InstockRecord(BaseModel):
    id: Optional[int]
    instock_item_id: int
    amount_in: int
    balance: int
    operator: str
    record_time: datetime
    note: Optional[str]
    display: dict = None

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str
    disabled: bool = False
    role: str


class User(UserBase):
    hashed_pwd: str

    class Config:
        orm_mode = True


# token url相应模型
class Token(BaseModel):
    access_token: str
    token_type: str


# 令牌数据模型
class TokenData(BaseModel):
    username: str = None
