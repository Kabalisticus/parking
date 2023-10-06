from typing import Optional
from pydantic import BaseModel, validator, constr, condecimal
from uuid import UUID
from enum import Enum
from datetime import date

from starlette.exceptions import HTTPException 
from starlette.status import HTTP_400_BAD_REQUEST



class PlateNumber(BaseModel):
    """
    Pydantic model for a plate number.

    Attributes:
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
    """
    plate_number: constr(regex=r'^[A-Z]{2,3}-[A-Z0-9]{4,5}$')

class DateValidated(BaseModel):
    """
    Pydantic model for validating a date range.

    Attributes:
        start_date (date): The start date of the date range.
        end_date (date): The end date of the date range.

    Validators:
        - Validates that the 'end_date' is not earlier than the 'start_date'.
          Raises an HTTP 400 Bad Request exception with a detail message
          if the validation fails.

    Example:
        To use this model, create an instance with 'start_date' and 'end_date'
        properties, and it will automatically validate the date range.

        ```python
        date_range = DateValidated(start_date="2023-01-01", end_date="2023-01-31")
        ```

    Raises:
        HTTPException: If 'end_date' is earlier than 'start_date', a 400 Bad Request
        HTTP exception is raised with the detail message "End date cannot be
        earlier than start date."

    """
    start_date: date
    end_date: date

    @validator("end_date", pre=False, always=True)
    def validate_dates(cls,end_date,values):
        start_date = values.get("start_date")

        if end_date <= start_date:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,            
                detail="End date cannot be earlier than start date"
                )
        return end_date
    

class PaymentStatus(str, Enum):
    """
    Enum representing payment statuses.

    Possible values:
        - "expects": Payment is expected.
        - "completed": Payment is completed.
    """
    expects="Oczekuje"
    completed="Zakonczono"

class SubscriptionRequest(PlateNumber,DateValidated):
    """
    Pydantic model for a subscription request.

    Attributes:
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
        start_date (date): The start date of the subscription.
        end_date (date): The end date of the subscription.
    """


class ExitRequest (PlateNumber):
    """
    Pydantic model for a exit request.

    Attributes:
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
        date_exit (date): The date of departure from the parking.
    """
    exit_date: date

class EntryRequest (PlateNumber):
    """
    Pydantic model for an entry request.

    Attributes:
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
        date_entry (date): The date of entry to the parking.
    """
    date_entry: date

class PaymentRequest (BaseModel):
    """
    Pydantic model for a payment request.

    Attributes:
        ticket_number (int): The number of ticket to be paid for.
        payment_value (decimal.Decimal): The value paid for the ticket.
        date_payment (date): The date of the payment.
    """
    ticket_number: int
    payment_value: condecimal(max_digits=4, decimal_places=2)
    date_payment: date 

class EarningsRequest(DateValidated):
    """
    Pydantic model for a earnings request.

    Attributes:
        start_date (date): The start date for earnings check.
        end_date (date): The end date for earnings check.
    """

class Subscription(PlateNumber,DateValidated):
    """
    Pydantic model for a subscription.

    Attributes:
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
        subscription_ID (int): The ID of the subscription.
        start_date (date): The start date of the subscription.
        end_date (date): The end date of the subscription.
    """
    subscription_ID: int

class Vehicle(PlateNumber):
    """
    Pydantic model for a vehicle.

    Attributes:
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
        vehicle_ID (UUID): The unique identifier for the vehicle.
    """
    vehicle_ID: UUID

class EntryExitRegister(PlateNumber):
    """
    Pydantic model for an entry/exit registration.

    Attributes:
        plate_number (str): The plate number in the format 'XX-XXXX' or 'XXX-XXXXX'.
        ticket_ID (UUID): The unique identifier for the ticket.
        entry_time (date): The date and time of entry.
        exit_time (Optional[date]): The date and time of exit (optional).
        amount (str): The payment amount in the format 'X.XX'.
        payment_status (PaymentStatus): The status of payment.

    Validators:
        - Validates that 'exit_time' is not earlier than 'entry_time'.
          Raises an HTTP 400 Bad Request exception with a detail message
          if the validation fails.

    Example:
        To use this model, create an instance with the specified attributes,
        and it will automatically validate the exit time.

        ```python
        entry_exit_data = EntryExitRegister(
            plate_number="XX-XXXX",
            ticket_ID=uuid.uuid4(),
            entry_time="2023-01-01",
            exit_time="2023-01-02",
            amount="10.50",
            payment_status="completed"
        )
        ```
    Raises:
        HTTPException: If 'exit_time' is earlier than 'entry_time', a 400 Bad Request
        HTTP exception is raised with the detail message "Exit time cannot be
        earlier than entry time."
    """

    ticket_ID: UUID
    entry_time: date 
    exit_time: Optional [date]
    amount: condecimal(max_digits=4, decimal_places=2)
    payment_status: PaymentStatus

    @validator("exit_time", pre=False, always=True)
    def validate_dates(cls,exit_time,values):
        entry_time = values.get("entry_time")

        if exit_time <= entry_time:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,            
                detail="End date cannot be earlier than start date"
                )
        return exit_time

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
    amount: condecimal(max_digits=4, decimal_places=2)
    payment_status: PaymentStatus