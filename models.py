from typing import Optional
from pydantic import BaseModel, constr
from uuid import UUID, uuid4
from enum import Enum

from datetime import date
from fastapi import FastAPI

app = FastAPI()

class SubscriptionRequest(BaseModel):
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    date_start: date  
    date_end: date

class ExitRequest (BaseModel):
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    date_exit: date
    date_payment: date

class PaymentsRequest (BaseModel):
    date_start: date
    date_end: date
    

class EntryRequest (BaseModel):
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    date_entry: date


class Subscribtion(BaseModel):
    subscribtion_ID: int
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    start_date: date
    end_date: date

class Payment_status(str, Enum):
    expects="Oczekuje"
    completed="Zakonczono"

class Vehicle(BaseModel):
    vehicle_ID: UUID
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')


class Entry_exit_register(BaseModel):
    ticket_ID: UUID
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    entry_time: date 
    exit_time: Optional [date]
    amount: constr(regex=r'^\d+\.\d{2}$')
    payment_status: Payment_status

class Payments(BaseModel):
    payment_ID: UUID
    ticket_number: int
    amount: constr(regex=r'^\d+\.\d{2}$')
    payment_status: Payment_status

    