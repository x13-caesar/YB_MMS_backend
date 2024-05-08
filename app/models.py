# coding=utf-8
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Integer,
    Boolean,
    String,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.ext.hybrid import hybrid_property
from app.database import Base
from sqlalchemy import select


class Vendor(Base):
    __tablename__ = "vendor"
    extend_existing = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    company = Column(String)
    payment_period = Column(String)
    contact = Column(String)
    address = Column(String)
    email = Column(String)
    fax = Column(String)
    notice = Column(String)

    @hybrid_property
    def display_id(self):
        return str(self.id).rjust(3, '0')


class Component(Base):
    __tablename__ = "component"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, ForeignKey("compo_category.category"))  # 分类
    model = Column(String)  # 型号
    description = Column(String)
    expiration = Column(String)
    as_unit = Column(String)  # 库存单位
    unit_weight = Column(String)  # 单位重量
    warn_stock = Column(Integer)
    picture = Column(String)
    notice = Column(String)
    fill_period = Column(String)
    hide = Column(Boolean)


class CompoCategory(Base):
    __tablename__ = "compo_category"

    id = Column(Integer, primary_key=True)
    category = Column(String)
    prefix = Column(String)


class Specification(Base):
    __tablename__ = "specification"

    id = Column(String, primary_key=True)
    component_id = Column(Integer, ForeignKey("component.id"))
    vendor_id = Column(Integer, ForeignKey("vendor.id"))
    gross_price = Column(Float)  # 含税价
    net_price = Column(Float)  # 税前价
    use_net = Column(Boolean, nullable=False, default=True)  # 采购使用税前价格
    stock = Column(Integer)
    unit_amount = Column(Integer)
    blueprint = Column(String)
    notice = Column(String)
    component = relationship("Component", back_populates="specification")
    vendor = relationship("Vendor", backref="specification")
    hide = Column(Boolean)

    @hybrid_property
    def display_vendor_id(self):
        return str(self.vendor_id).rjust(3, '0')


Component.specification = relationship(
    "Specification", order_by=Specification.id, back_populates="component"
)


class Buyer(Base):
    __tablename__ = "buyer"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    company = Column(String)
    payment_period = Column(String)
    contact = Column(String)
    address = Column(String)
    notice = Column(String)


class Product(Base):
    __tablename__ = "product"

    id = Column(String, primary_key=True)
    name = Column(String)
    category = Column(String)
    description = Column(String)
    inventory = Column(Integer)
    picture = Column(String)
    custom = Column(String)
    notice = Column(String)
    deprecated = Column(Boolean)
    deprecated_date = Column(DateTime)


class ProductCategory(Base):
    __tablename__ = "product_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String, nullable=False)


class Process(Base):
    __tablename__ = "process"

    id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey("product.id"))
    process_name = Column(String)
    process_order = Column(Integer)
    notice = Column(String)
    unit_pay = Column(Float)
    process_component = relationship("ProcessComponent", backref="process")


Product.process = relationship("Process", order_by=Process.id, backref="product")


class ProcessComponent(Base):
    __tablename__ = "process_component"

    id = Column(Integer, primary_key=True)
    process_id = Column(String, ForeignKey("process.id"))
    component_id = Column(String, ForeignKey("component.id"))
    attrition_rate = Column(Float)
    consumption = Column(Integer)
    component = relationship("Component", backref="process_component")


class Batch(Base):
    __tablename__ = "batch"

    id = Column(Integer, primary_key=True)
    status = Column(String)
    product_id = Column(String, ForeignKey("product.id"))
    plan_amount = Column(Integer)
    actual_amount = Column(Integer)
    create = Column(DateTime)
    start = Column(DateTime)
    end = Column(DateTime)
    ship = Column(DateTime)
    notice = Column(String)
    product_name = column_property(
        select(Product.name).where(Product.id == product_id).scalar_subquery()
    )


class BatchProcess(Base):
    __tablename__ = "batch_process"

    id = Column(Integer, primary_key=True)
    status = Column(String)
    process_id = Column(String, ForeignKey("process.id"))
    batch_id = Column(Integer, ForeignKey("batch.id"))
    start_amount = Column(Integer)
    end_amount = Column(Integer)
    unit_pay = Column(Float)
    warehouse_record = relationship("WarehouseRecord", backref="batch_process")
    process = relationship("Process", backref="batch_process", lazy="joined")


Batch.batch_process = relationship(
    "BatchProcess", order_by=BatchProcess.id, backref="batch", lazy="joined"
)

# Process.batch_process = relationship("BatchProcess",
#                                      order_by=BatchProcess.id,
#                                      backref="process")


class Delivery(Base):
    __tablename__ = "delivery"

    id = Column(Integer, primary_key=True)
    product_id = Column(String, ForeignKey("product.id"))
    amount = Column(Integer)
    order_id = Column(String)
    buyer_id = Column(Integer, ForeignKey("buyer.id"))
    deliver_date = Column(Date)
    unit_price = Column(Float)
    total_price = Column(Float)
    reconciled = Column(Boolean, default=False)
    paid = Column(Boolean, default=False)
    notice = Column(String)
    product = relationship("Product", back_populates="delivery")
    buyer = relationship("Buyer", back_populates="delivery")


Product.delivery = relationship(
    "Delivery", order_by=Delivery.id, back_populates="product"
)


Buyer.delivery = relationship("Delivery", order_by=Delivery.id, back_populates="buyer")


class Operation(Base):
    __tablename__ = "operation"

    id = Column(Integer, primary_key=True)
    content = Column(String)
    operator = Column(String)
    execute_time = Column(DateTime)


class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    gender = Column(String)
    birth = Column(DateTime)
    phone = Column(String)
    ssn = Column(String)
    department = Column(String)
    status = Column(String)
    onboard = Column(DateTime)
    notice = Column(String)
    last_pay_check = Column(DateTime)


class Salary(Base):
    __tablename__ = "salary"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employee.id"))
    employee_name = Column(String, ForeignKey("employee.name"))
    start_date = Column(Date)
    end_date = Column(Date)
    unit_salary = Column(Float)
    hour_salary = Column(Float)
    deduction = Column(Float)
    bonus = Column(Float)
    status = Column(String)
    notice = Column(String)
    check_date = Column(DateTime)
    day_invoice = relationship("DayInvoice", backref="salary")
    work = relationship("Work", backref="salary", lazy="joined")


class Work(Base):
    __tablename__ = "work"

    id = Column(Integer, primary_key=True)
    batch_process_id = Column(Integer, ForeignKey("batch_process.id"))
    employee_id = Column(Integer, ForeignKey("employee.id"))
    employee_name = Column(String, ForeignKey("employee.name"))
    work_date = Column(Date)
    unit_pay = Column(Float)
    complete_unit = Column(Integer)
    hour_pay = Column(Float)
    complete_hour = Column(Integer)
    plan_unit = Column(Integer)
    check = Column(Boolean)
    salary_id = Column(Integer, ForeignKey("salary.id"))
    product_name = Column(String, ForeignKey("product.name"))
    process_name = Column(String, ForeignKey("process.process_name"))


BatchProcess.work = relationship(
    "Work", order_by=Work.id, backref="batch_process", lazy="joined"
)


class WorkSpecification(Base):
    __tablename__ = "work_specification"

    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, ForeignKey("work.id"))
    specification_id = Column(String, ForeignKey("specification.id"))
    plan_amount = Column(Integer)
    actual_amount = Column(Integer)
    component_name = Column(String)
    specification_net_price = Column(Float)
    specification_gross_price = Column(Float)


Work.work_specification = relationship(
    "WorkSpecification", order_by=WorkSpecification.id, backref="work"
)


class User(Base):
    __tablename__ = "user"

    username = Column(String, primary_key=True)
    hashed_pwd = Column(String)
    disabled = Column(Boolean)
    role = Column(String)


class WarehouseRecord(Base):
    __tablename__ = "warehouse_record"

    id = Column(Integer, primary_key=True)
    batch_process_id = Column(Integer, ForeignKey("batch_process.id"))
    component_id = Column(String, ForeignKey("component.id"))
    specification_id = Column(String, ForeignKey("specification.id"))
    component_name = Column(String, ForeignKey("component.name"))
    consumption = Column(Integer)
    specification_net_price = Column(Float)
    specification_gross_price = Column(Float)


class DayInvoice(Base):
    __tablename__ = "day_invoice"

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("batch.id"))
    process_name = Column(String)
    employee_id = Column(Integer, ForeignKey("employee.id"))
    employee_name = Column(String)
    work_date = Column(DateTime)
    unit_pay = Column(Float)
    complete_unit = Column(Integer)
    hour_pay = Column(Float)
    complete_hour = Column(Integer)
    check_status = Column(Boolean)
    check_date = Column(DateTime)
    salary_id = Column(Integer, ForeignKey("salary.id"))


class InstockForm(Base):
    __tablename__ = "instock_form"

    form_id = Column(Integer, primary_key=True)
    display_form_id = Column(String)
    vendor_id = Column(Integer, ForeignKey("vendor.id"))
    create_time = Column(DateTime)
    form_status = Column(String)
    amount = Column(Float)
    note = Column(String)
    paid = Column(Boolean)
    vendor = relationship("Vendor", back_populates="instock_form", lazy="joined")


Vendor.instock_form = relationship(
    "InstockForm", order_by=InstockForm.form_id, back_populates="vendor"
)


class InstockItem(Base):
    __tablename__ = "instock_item"

    instock_item_id = Column(Integer, primary_key=True, autoincrement=True)
    form_id = Column(Integer, ForeignKey("instock_form.form_id"))
    specification_id = Column(String, ForeignKey("specification.id"))
    order_quantity = Column(Integer)
    unit_cost = Column(Float)
    warehouse_quantity = Column(Integer)
    last_time = Column(DateTime)
    instock_date = Column(Date)  # 预计到货日期
    vendor_instock_date = Column(Date)  # 供应商回复交期
    notice = Column(String)
    instock_form = relationship("InstockForm", back_populates="instock_item", lazy="joined")

    # # Define a property to access the display_form_id attribute
    # @property
    # def display_form_id(self):
    #     return self.instock_form.display_form_id
    #
    # # Define a setter for the display_form_id attribute
    # @display_form_id.setter
    # def display_form_id(self, value):
    #     self.instock_form.display_form_id = value


InstockForm.instock_item = relationship(
    "InstockItem",
    order_by=InstockItem.form_id,
    back_populates="instock_form",
    lazy="joined",
)


class InstockRecord(Base):
    __tablename__ = "instock_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instock_item_id = Column(Integer, ForeignKey("instock_item.instock_item_id"))
    amount_in = Column(Integer, nullable=False)
    balance = Column(Integer, nullable=False)
    operator = Column(String)
    record_time = Column(DateTime, nullable=False)
    note = Column(String)
