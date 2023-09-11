from typing import Optional, List
from pydantic import BaseModel, constr
from uuid import UUID, uuid4
from enum import Enum


class Payment_status(str, Enum):
    expects="Oczekuje"
    completed="Zakonczono"

class Vehicle(BaseModel):
    vehicle_ID: UUID
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')


class Entry_exit_register(BaseModel):
    ticket_ID: UUID
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    entry_time: str 
    exit_time: Optional [str]
    amount: constr(regex=r'^\d+\.\d{2}$')
    payment_status: Payment_status


class Subscribtion(BaseModel):
    subscribtion_ID: UUID
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    start_date: str 
    end_date: str

class Payments(BaseModel):
    payment_ID: UUID
    ticket_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    amount: constr(regex=r'^\d+\.\d{2}$')
    payment_status: Payment_status

    