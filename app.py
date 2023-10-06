import asyncpg
from fastapi import FastAPI
from datetime import date

from starlette.exceptions import HTTPException 
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE, HTTP_400_BAD_REQUEST

from models import SubscriptionRequest, EntryRequest, ExitRequest, PaymentRequest

TARIFF = 5
ALL_PARKING_SPOTS = 50

app = FastAPI()

DATABASE_URL = "postgresql://parking:123test@localhost:5432/parking"


@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(DATABASE_URL)


@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()


@app.post("/payments/subscribe")
async def register_subsctibtion(subscription_input: SubscriptionRequest):
    '''
    Register a new subscription.

    :param subscription_input: The subscription request data.
    :type subscription_input: SubscriptionRequest

    :return: A dictionary with a success message and subscription details.
    :rtype: dict
    '''
    async with app.state.pool.acquire() as connection:

        # Add new entry to the 'pojazdy' table, do nothing when record already exists
        vehicyle_insert_query = """
        INSERT INTO pojazdy (numer_rejestracyjny)
        VALUES ($1)
        ON CONFLICT DO NOTHING"""
        await connection.execute(vehicyle_insert_query, subscription_input.plate_number)

        # Add new entry to the 'abonamenty' table
        subscription_insert_query = """ 
        INSERT INTO abonamenty (numer_rejestracyjny, data_rozpoczecia, data_zakonczenia)
        VALUES ($1, $2, $3)
        """
        await connection.execute(subscription_insert_query, subscription_input.plate_number,
                                  subscription_input.start_date, subscription_input.end_date)

        return {
                "message": "New subscribtion successfully registered",
                "subscribtion_start_date:": subscription_input.start_date,
                "subscribtion_end_date: ": subscription_input.end_date,
                "plate_number: ": subscription_input.plate_number}

# Register a new entry on the parking
@app.post("/register/enter")
async def register_entry (entry_input: EntryRequest):
    '''
    Register a new entry on the parking.

    :param entry_input: The entry request data.
    :type entry_input: EntryRequest

    :return: A dictionary with a success message.
    :rtype: dict
    '''
    async with app.state.pool.acquire() as connection:

        # Check if there are any free parking spots available
        free_spots_value = await free_spots()
        if free_spots_value["free_spots"] <= 0:
            raise HTTPException(
                status_code=HTTP_503_SERVICE_UNAVAILABLE,
                detail="No parking spots available. Please try again later"
            )

        # Add new entry to the 'pojazdy' table, do nothing when record already exists
        vehicyle_insert_query = """
        INSERT INTO pojazdy (numer_rejestracyjny)
        VALUES ($1)
        ON CONFLICT DO NOTHING"""
        await connection.execute(vehicyle_insert_query, entry_input.plate_number)

        # Add new entry to rejestr wjazdu wyjazdu table
        register_entry_insert_query = """ 
        INSERT INTO rejestr_wjazdu_wyjazdu
        (numer_rejestracyjny, czas_wjazdu,czas_wyjazdu, kwota, status_platnosci)
        VALUES ($1, $2, NULL, 0, 'Oczekuje')
        """
        await connection.execute(register_entry_insert_query,
                                 entry_input.plate_number, entry_input.date_entry)
    
        return {"message": "New entry registered succesfuly"}


@app.post("/register/exit")
async def register_exit(exit_input: ExitRequest):
    '''
    Register the exit of a vehicle from the parking.

    :param exit_input: The exit request data.
    :type exit_input: ExitRequest

    :return: A dictionary with a message, ticket number, and payment amount.
    :rtype: dict
    '''
    async with app.state.pool.acquire() as connection:
        

        # Subscribtion end date 
        end_date_query = """
        SELECT a.data_zakonczenia::date
        FROM abonamenty a
        WHERE a.numer_rejestracyjny = $1 AND a.data_zakonczenia IS NOT NULL
        """
        subscription_end_date = await connection.fetchval(end_date_query, exit_input.plate_number)

        # Subscribtion start date
        start_date_query = """
        SELECT a.data_rozpoczecia::date
        FROM abonamenty a
        WHERE a.numer_rejestracyjny = $1 AND a.data_rozpoczecia IS NOT NULL
        """
        subscription_start_date = await connection.fetchval(start_date_query, exit_input.plate_number)
        
        # Entry date 
        entry_date_query = """
        SELECT rww.czas_wjazdu
        FROM rejestr_wjazdu_wyjazdu rww
        WHERE rww.numer_rejestracyjny = $1 AND rww.czas_wyjazdu IS NULL
        """
        entry_date = await connection.fetchval(entry_date_query, exit_input.plate_number)

        # Check if there is entry record with such input data
        if entry_date is None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="No matching entry record found. Please wait for the Police"
            )
        
        # Ticket number 
        ticket_number_query = """
        SELECT rww.numer_wydruku
        FROM rejestr_wjazdu_wyjazdu rww
        WHERE rww.numer_rejestracyjny = $1 AND rww.czas_wyjazdu IS NULL
        """
        ticket_number = await connection.fetchval(ticket_number_query, exit_input.plate_number)

        # Check if there is ticket with such input data
        if ticket_number is None:
                raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="No matching ticket number found"
            )

        # Check for the subscription status on entry
        subscription_entry_status_query = """
        SELECT rww.numer_wydruku
        FROM rejestr_wjazdu_wyjazdu rww
        JOIN abonamenty a ON rww.numer_rejestracyjny=a.numer_rejestracyjny
        WHERE rww.numer_rejestracyjny=$1 AND
        rww.czas_wjazdu BETWEEN a.data_rozpoczecia AND a.data_zakonczenia
        """ 
        subscribtion_active_entry = await connection.fetchval(
            subscription_entry_status_query, exit_input.plate_number
        )

        if subscribtion_active_entry is not None:
            subscribtion_active_entry = True
        else:
            subscribtion_active_entry = False

        # Check for the subscription status on exit
        subscription_exit_status_query = """
        SELECT rww.numer_wydruku
        FROM rejestr_wjazdu_wyjazdu rww
        JOIN abonamenty a ON rww.numer_rejestracyjny=a.numer_rejestracyjny
        WHERE rww.numer_rejestracyjny=$1 AND
        $2 BETWEEN a.data_rozpoczecia AND a.data_zakonczenia
        """ 
        subscribtion_active_exit = await connection.fetchval(
            subscription_exit_status_query, exit_input.plate_number, exit_input.exit_date
        )
        if subscribtion_active_exit is not None:
            subscribtion_active_exit = True
        else: 
            subscribtion_active_exit= False

        #Defaults for payment cases:
        amount_to_pay = 0.00
        payment_status = "Oczekuje"
        return_message = f"Ticket number: {ticket_number} Parking fee: {amount_to_pay}"

        # Payment cases depending on subscription status
        if subscribtion_active_entry and subscribtion_active_exit:
            return_message = "You are free to go, please visit us again!"
            payment_status = 'Zakonczono'

        elif subscribtion_active_entry and not subscribtion_active_exit:
            amount_to_pay = (subscription_end_date - entry_date).days * TARIFF
        
        elif not subscribtion_active_entry and not subscribtion_active_exit:
            amount_to_pay = (exit_input.exit_date - entry_date).days * TARIFF

        else:
            amount_to_pay = (subscription_start_date - entry_date).days * TARIFF

        # Update the 'rejestr_wjazdu_wyjazdu' table
        register_update_query = """
        UPDATE rejestr_wjazdu_wyjazdu
        SET 
            czas_wyjazdu = $1,
            kwota = $3,
            status_platnosci = $4
        WHERE numer_rejestracyjny = $2 AND czas_wyjazdu IS NULL
        """
        await connection.execute(register_update_query, exit_input.exit_date, exit_input.plate_number, amount_to_pay, payment_status)
        
        return {"message": return_message, 
                "ticket_number": ticket_number,
                "pay_amount": amount_to_pay}    


@app.post("/payments/onetime")
async def register_payment(payment_input: PaymentRequest):
    '''
    Register a one-time payment for parking.

    :param payment_input: The payment request data.
    :type payment_input: PaymentRequest

    :return: A dictionary with a message, ticket number, and remaining payment amount.
    :rtype: dict
    '''
    async with app.state.pool.acquire() as connection:
    

        # Check the 'rejestr_wjazdu_wyjazdu' for value to pay for parking
        ticket_value_query = """
        SELECT rww.kwota::decimal
        FROM rejestr_wjazdu_wyjazdu rww
        WHERE rww.numer_wydruku = $1
        """
        ticket_value = await connection.fetchval(ticket_value_query, payment_input.ticket_number)
        
        # Check if the is ticket meeting those criteria
        if ticket_value is None:
            raise HTTPException(
                status_code = HTTP_400_BAD_REQUEST,
                detail = "No matching ticket number found"
            )

        # Check if any payments were done for this ticket and sum them up
        already_paid_query="""
        SELECT (
        SELECT COALESCE(SUM(kwota::decimal), 0)
        FROM platnosci_jednorazowe p
        WHERE p.numer_wydruku = $1 and p.status_platnosci = 'Zakonczono'
        ) AS total_amount
        """
        already_paid = await connection.fetchval(already_paid_query, payment_input.ticket_number)

        # Calculate the value that left to pay
        left_to_pay = ticket_value - already_paid

        # Check if ticket has already been paid
        if not left_to_pay:
                raise HTTPException(
                status_code = HTTP_400_BAD_REQUEST,
                detail = "The ticket has already been paid. Check your ticket number and try again"
            )

        #Add a new entry on 'platnosci_jednorazowe' table
        insert_payment_query = """
        INSERT INTO platnosci_jednorazowe (numer_wydruku, kwota, status_platnosci, data_platnosci)
        VALUES ($1, $2, 'Zakonczono', $3)
        """
        await connection.execute(insert_payment_query, payment_input.ticket_number, 
                                 payment_input.payment_value, payment_input.date_payment)

        if payment_input.payment_value == left_to_pay:

            # Update the 'status_platnosci' record in 'rejestr_wjazdu_wyjazdu' table  
            update_rww_query = """
            UPDATE rejestr_wjazdu_wyjazdu
            SET status_platnosci = 'Zakonczono'
            WHERE numer_wydruku = $1
            """
            await connection.execute(update_rww_query,payment_input.ticket_number)

            return_message = "You're free to go, Please visit us again"

        elif payment_input.payment_value<left_to_pay:

            ticket_value=left_to_pay-payment_input.payment_value
            return_message = f"Additional payment is required. Amount due: {ticket_value}" 

        elif payment_input.payment_value > left_to_pay:
            return_message = "You've overpaid. Please contact us under phone number 0700-88-07-88"
   
        return {"message": return_message, 
                "ticket_number": payment_input.ticket_number,
                "pay_amount": ticket_value}   


@app.get("/stats/free-spots")
async def free_spots():
    '''
    Calculate the number of free parking spots.

    :return: A dictionary with the number of free spots.
    :rtype: dict
    '''
    async with app.state.pool.acquire() as connection:

        #calculate all of the parked vehicles
        parked_all_query = """
        SELECT COUNT(czas_wjazdu)
        FROM rejestr_wjazdu_wyjazdu
        WHERE czas_wyjazdu IS NULL;
        """   
        parked_all = await connection.fetchval(parked_all_query)

        #calculate number of the parked vehicles with active subscribtion
        parked_subscribtion_query = """
        SELECT COUNT(czas_wyjazdu)
        FROM rejestr_wjazdu_wyjazdu rww
        JOIN pojazdy p ON rww.numer_rejestracyjny = p.numer_rejestracyjny
        JOIN abonamenty a ON p.numer_rejestracyjny = a.numer_rejestracyjny
        WHERE rww.czas_wyjazdu IS NULL
        AND CURRENT_DATE BETWEEN a.data_rozpoczecia AND a.data_zakonczenia;
        """
        parked_subscribtion = await connection.fetchval(parked_subscribtion_query)
        
        #calculate number of all vehicles with active subscribtion
        all_subscribtion_query = """
        SELECT COUNT(numer_subskrybcji)
        FROM abonamenty a
        JOIN pojazdy p ON p.numer_rejestracyjny = a.numer_rejestracyjny
        WHERE CURRENT_DATE BETWEEN a.data_rozpoczecia AND a.data_zakonczenia;
        """    
        all_subscribtion = await connection.fetchval(all_subscribtion_query)

        #calculate number of free spots 
        free_spots = ALL_PARKING_SPOTS - parked_all + parked_subscribtion - all_subscribtion
        
        return {"free_spots": free_spots}


@app.get("/stats/financial")
async def get_earnings(start_date: date, end_date: date):
    '''
    Calculate the financial earnings for a specified date range.

    :param date_start: The start date of the earnings calculation.
    :type date_start: date
    :param date_end: The end date of the earnings calculation.
    :type date_end: date

    :return: A dictionary with total earnings, one-time payment earnings, and subscription earnings.
    :rtype: dict
    '''
    async with app.state.pool.acquire() as connection:

        # Date order validation 
        if end_date <= start_date:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="End date cannot be earlier than start date"
            )


        #Calculate the revenues from single payments
        earnigns_onetime_query = """
            SELECT COALESCE(SUM(kwota), 0)
            FROM platnosci_jednorazowe 
            WHERE data_platnosci BETWEEN $1 AND $2
        """
        earnings_onetime = await connection.fetchval(earnigns_onetime_query, start_date, end_date)

        # Calculate the revenues from subscribtions
        earnings_subscribtions_query = """
            SELECT COALESCE(SUM(EXTRACT(YEAR FROM age(data_zakonczenia, data_rozpoczecia)) * 12 
            + EXTRACT(MONTH FROM age(data_zakonczenia, data_rozpoczecia))) * 100, 0)
            FROM abonamenty
            WHERE data_rozpoczecia >= $1 AND data_zakonczenia <= $2
        """ 
        earnings_subscribtions = await connection.fetchval(earnings_subscribtions_query, start_date, end_date)

        # Calculate the sum of the revenues 
        earnings_total = earnings_onetime + earnings_subscribtions

        return {
            "earnings_total": earnings_total,
            "earnings_onetime": earnings_onetime,
            "earnings_subscribtions": earnings_subscribtions
        }