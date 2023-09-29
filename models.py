from typing import Optional
from pydantic import BaseModel, constr, condecimal
from uuid import UUID
from enum import Enum
from datetime import date
from fastapi import FastAPI

app = FastAPI()

class PlateNumber(BaseModel):
    """
    Pydantic model for a plate number.

    Attributes:
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
    """
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')

class PaymentStatus(str, Enum):
    """
    Enum representing payment statuses.

    Possible values:
        - "expects": Payment is expected.
        - "completed": Payment is completed.
    """
    expects="Oczekuje"
    completed="Zakonczono"

class SubscriptionRequest(PlateNumber):
    """
    Pydantic model for a subscription request.

    Attributes:
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
        date_start (date): The start date of the subscription.
        date_end (date): The end date of the subscription.
    """
    date_start: date  
    date_end: date

class ExitRequest (PlateNumber):
    """
    Pydantic model for a exit request.

    Attributes:
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
        date_exit (date): The date of departure from the parking.
    """
    exit_date: date

class PaymentRequest (BaseModel):
    """
    Pydantic model for a payment request.

    Attributes:
        ticket_number (int): The number of ticket to be paid for.
        payment_value (decimal.Decimal): The value paid for the ticket.
        date_payment (date): The date of the payment.
    """
    ticket_number: int
    payment_value: condecimal(max_digits=10, decimal_places=2)
    date_payment: date 

class EntryRequest (BaseModel):
    """
    Pydantic model for an entry request.

    Attributes:
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
        date_entry (date): The date of entry to the parking.
    """
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    date_entry: date
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    date_entry: date

class Subscription(BaseModel):
    """
    Pydantic model for a subscription.

    Attributes:
        subscription_ID (int): The ID of the subscription.
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
        start_date (date): The start date of the subscription.
        end_date (date): The end date of the subscription.
    """
    subscription_ID: int
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    start_date: date
    end_date: date

class Vehicle(BaseModel):
    """
    Pydantic model for a vehicle.

    Attributes:
        vehicle_ID (UUID): The unique identifier for the vehicle.
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
    """
    vehicle_ID: UUID
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')


class EntryExitRegister(BaseModel):
    """
    Pydantic model for an entry/exit registration.

    Attributes:
        ticket_ID (UUID): The unique identifier for the ticket.
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
        entry_time (date): The date and time of entry.
        exit_time (Optional[date]): The date and time of exit (optional).
        amount (str): The payment amount in the format 'X.XX'.
        payment_status (PaymentStatus): The status of payment.
    """
    ticket_ID: UUID
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')
    entry_time: date 
    exit_time: Optional [date]
    amount: condecimal(max_digits=10, decimal_places=2)
    payment_status: PaymentStatus

class Payments(BaseModel):
    """
    Pydantic model for payments.

    Attributes:
        payment_ID (UUID): The unique identifier for the payment.
        ticket_number (int): The ticket number associated with the payment.
        amount (str): The payment amount in the format 'X.XX'.
        payment_status (PaymentStatus): The status of payment.
    """
    payment_ID: UUID
    ticket_number: int
    amount: condecimal(max_digits=10, decimal_places=2)
    payment_status: PaymentStatus