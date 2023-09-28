
from datetime import date, datetime
from fastapi import FastAPI
from models import SubscriptionRequest, EntryRequest, ExitRequest, PaymentRequest
import asyncpg

tariff = 5
all_parking_spots = 50

app = FastAPI()

DATABASE_URL = "postgresql://parking:123test@localhost:5432/parking"


@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(DATABASE_URL)

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()

#Register a new subscibtion
@app.post("/payments/subscribe")
async def register_subsctibtion(subscribtion_input: SubscriptionRequest):
    async with app.state.pool.acquire() as connection:

        plate_number = subscribtion_input.plate_number
        date_start = subscribtion_input.date_start
        date_end = subscribtion_input.date_end

        # UPSERT insert into pojazdy (numer_rejestracyjny) values ('1223') on CONFLICT DO NOTHING; 
        # Check if the vehicle is already in database:
        vehicyle_exists_query = "SELECT 1 FROM pojazdy WHERE numer_rejestracyjny = $1"
        vehicyle_exists = await connection.fetchval(vehicyle_exists_query, plate_number)
        # If vevicle is not present
        if not vehicyle_exists:

            # Update the sequence counter for pojazdy
            await connection.execute("SELECT setval('pojazdy_numer_pojazdu_seq', (SELECT max(numer_pojazdu) FROM pojazdy))")

            # Add new entry to the pojazdy database
            vehicyle_insert_query = """
            INSERT INTO pojazdy (numer_rejestracyjny) VALUES ($1)"""

            await connection.execute(vehicyle_insert_query, plate_number)
            
        # Update sequence counter for rejestr_wjazdu_wyjazdu
        await connection.execute("SELECT setval('rejestr_wjazdu_wyjazdu_numer_wydruku_seq', (SELECT max(numer_wydruku) FROM rejestr_wjazdu_wyjazdu))")
        
        # Add new entry to the abonamenty table
        subscribtion_insert_query = """
            INSERT INTO abonamenty (numer_rejestracyjny, data_rozpoczecia, data_zakonczenia)
            VALUES ($1, $2, $3)
        """
        await connection.execute(subscribtion_insert_query, plate_number, date_start, date_end)

        return {"message": "New subscribtion successfully registered",
                "Subscribtion start:": date_start,
                "Subscribtion end: ": date_end,
                "Vehicle plate number: ": plate_number }

# Register a new entry on the parking
@app.post("/register/enter")
async def register_entry (entry_input: EntryRequest):
    async with app.state.pool.acquire() as connection:

        plate_number = entry_input.plate_number
        date_entry = entry_input.date_entry

        # Check if the vehicle is already in the database
        vehicyle_exists_query = "SELECT 1 FROM pojazdy WHERE numer_rejestracyjny = $1"
        vehicyle_exists = await connection.fetchval(vehicyle_exists_query, plate_number)

        if not vehicyle_exists:

        # Update the sequence counter for Pojazdy table
            await connection.execute("SELECT setval('pojazdy_numer_pojazdu_seq', (SELECT max(numer_pojazdu) FROM pojazdy))")
        
        #Update sequence counter for Rejestr_wjazdu_wyjazdu table 
            await connection.execute("SELECT setval('rejestr_wjazdu_wyjazdu_numer_wydruku_seq', (SELECT max(numer_wydruku) FROM rejestr_wjazdu_wyjazdu))")
        
        # Add new entry to Pojazdy table
            vehicyle_insert_query = """
            INSERT INTO pojazdy (numer_rejestracyjny) VALUES ($1)"""
            await connection.execute(vehicyle_insert_query, plate_number)

        # Add new entry to rejestr wjazdu wyjazdu table
            register_entry_insert_query = """ 
            INSERT INTO rejestr_wjazdu_wyjazdu (numer_rejestracyjny, czas_wjazdu, czas_wyjazdu, kwota, status_platnosci)
            VALUES ($1, $2, NULL, 0, 'Oczekuje')
        """
            await connection.execute(register_entry_insert_query, plate_number, date_entry)
    

        return {"message": "New entry registered succesfuly"}

# Register the exit of the vehicle    
@app.post("/register/exit")
async def register_exit(exit_input: ExitRequest):
    async with app.state.pool.acquire() as connection:

        plate_number = exit_input.plate_number
        date_exit = exit_input.date_exit

        #Assign values for the variables

        # Subscribtion end date 
        end_date_query = """
        SELECT a.data_zakonczenia::date
        FROM abonamenty a
        WHERE a.numer_rejestracyjny = $1 AND a.data_zakonczenia IS NOT NULL
        """
        subscribtion_end_date = await connection.fetchval(end_date_query, plate_number)

        # Subscribtion start date
        start_date_query = """
        SELECT a.data_rozpoczecia::date
        FROM abonamenty a
        WHERE a.numer_rejestracyjny = $1 AND a.data_rozpoczecia IS NOT NULL
        """
        subscribtion_start_date = await connection.fetchval(start_date_query, plate_number)
        
        # Entry date 
        entry_date_query = """
        SELECT rww.czas_wjazdu
        FROM rejestr_wjazdu_wyjazdu rww
        WHERE rww.numer_rejestracyjny = $1 AND rww.czas_wyjazdu IS NULL
        """
        entry_date = await connection.fetchval(entry_date_query, plate_number)

        # Ticket number 
        ticket_number_query = """
        SELECT rww.numer_wydruku
        FROM rejestr_wjazdu_wyjazdu rww
        WHERE rww.numer_rejestracyjny = $1 AND rww.czas_wyjazdu IS NULL
        """
        ticket_number = await connection.fetchval(
            ticket_number_query, plate_number
        )
        # Check for the subscription status on entry and exit
        try: 
            subscription_status_query = """
            SELECT
                CASE
                    WHEN rww.czas_wjazdu BETWEEN a.data_rozpoczecia AND a.data_zakonczenia THEN TRUE
                    ELSE FALSE
                END::BOOLEAN,
                CASE
                    WHEN a.data_zakonczenia >= $2 THEN TRUE
                    ELSE FALSE
                END::BOOLEAN
            FROM rejestr_wjazdu_wyjazdu rww
            JOIN pojazdy p ON rww.numer_rejestracyjny = p.numer_rejestracyjny
            JOIN abonamenty a ON p.numer_rejestracyjny = a.numer_rejestracyjny
            WHERE p.numer_rejestracyjny = $1 AND rww.czas_wyjazdu IS NULL
            """
            subscribtion_active_entry ,subscribtion_active_exit = await connection.fetchrow(
                subscription_status_query, plate_number, date_exit
            )
        except Exception as e:
            return f"Wrong plate number: {e}"
        

        # Cases depending on subscription status
        if subscribtion_active_entry and subscribtion_active_exit:
            amount_to_pay = 0
        elif subscribtion_active_entry and not subscribtion_active_exit:
            amount_to_pay = (subscribtion_end_date - entry_date).days * tariff
        elif not subscribtion_active_entry and not subscribtion_active_exit:
            amount_to_pay = (date_exit - entry_date).days * tariff
        else:
            amount_to_pay = (subscribtion_start_date - entry_date).days * tariff


        # Update the 'rejestr_wjazdu_wyjazdu' table

        register_update_query = """
        UPDATE rejestr_wjazdu_wyjazdu
        SET 
            czas_wyjazdu = $1,
            kwota = $3,
            status_platnosci = 'Oczekuje'
        WHERE numer_rejestracyjny = $2 AND czas_wyjazdu IS NULL
        
        """
        await connection.execute(register_update_query, date_exit, plate_number,amount_to_pay)
        
        return {"message": "Your ticket number and parking fee are: ", 
                "ticket_number": ticket_number,
                "pay_amount": amount_to_pay}    


@app.post("/payments/onetime")
async def register_payment(payment_input: PaymentRequest):
    async with app.state.pool.acquire() as connection:

        payment_value = payment_input.payment_value
        ticket_number = payment_input.ticket_number
        date_payment = payment_input.date_payment

        # Check the Rejestr Wjazdu Wyjazdu for value to pay for parking
        ticket_value_query = """
        SELECT rww.kwota
        FROM rejestr_wjazdu_wyjazdu rww
        WHERE rww.numer_wydruku = $1
        """
        ticket_value = await connection.fetchval(ticket_value_query, ticket_number)

        # Check if any payments were done for this ticket and sum them up
        already_payed_query="""
        SELECT COALESCE(SUM(kwota::decimal), 0)
        FROM platnosci_jednorazowe p
        WHERE p.numer_wydruku = $1 and p.status_platnosci = 'Zakonczono'
        """
        already_payed = await connection.fetchval(already_payed_query, ticket_number)

        if already_payed is None:
            already_payed = 0
        
        # Calculate the value that left to pay  
        left_to_pay = ticket_value - already_payed

        #Add a new entry on platnosci_jednorazowe table
        insert_payment_query = """
        INSERT INTO platnosci_jednorazowe (numer_wydruku, kwota, status_platnosci, data_platnosci)
        VALUES ($1, $2, 'Zakonczono', $3)
        """
        await connection.execute(
            insert_payment_query, ticket_number, payment_value, date_payment
        )

        if payment_value == left_to_pay:

            # Update the RWW status_platnosci record  
            update_rww_query = """
            UPDATE rejestr_wjazdu_wyjazdu
            SET status_platnosci = 'Zakonczono'
            WHERE numer_wydruku = $1
            """
            await connection.execute(
                update_rww_query,ticket_number
            )

            return_message = "You're free to go, Please visit us again"

        elif payment_value<left_to_pay:

            ticket_value=left_to_pay-payment_value
            return_message = f"Additional payment is required. Amount due: {ticket_value}" 

        elif payment_value > left_to_pay:
            return_message = "You've overpaid. Please contact us under phone number 0700-88-07-88"

        return {"message": return_message, 
                "ticket_number": ticket_number,
                "pay_amount": ticket_value}   


# Calculate the number of free spots on the parking

@app.get("/stats/free-spots")
async def free_spots():
    async with app.state.pool.acquire() as connection:

# Assign values to the variables

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
        free_spots = all_parking_spots - parked_all + parked_subscribtion - all_subscribtion
        
        return {"free_spots": free_spots}



@app.get("/stats/financial")

async def get_earnings(date_start: date, date_end: date):
    async with app.state.pool.acquire() as connection:

        #Calculate the revenues from single payments
        earnigns_onetime_query = """
            SELECT COALESCE(SUM(kwota), 0)
            FROM platnosci_jednorazowe 
            WHERE data_platnosci BETWEEN $1 AND $2
        """
        earnings_onetime = await connection.fetchval(earnigns_onetime_query, date_start, date_end)

        # Calculate the revenues from subscribtions
        earnings_subscribtions_query = """
            SELECT COALESCE(SUM(EXTRACT(YEAR FROM age(data_zakonczenia, data_rozpoczecia)) * 12 + EXTRACT(MONTH FROM age(data_zakonczenia, data_rozpoczecia))) * 100, 0)
            FROM abonamenty
            WHERE data_rozpoczecia >= $1 AND data_zakonczenia <= $2
        """ 
        earnings_subscribtions = await connection.fetchval(earnings_subscribtions_query, date_start, date_end)

        # Calculate the sum of the revenues 
        earnings_total = earnings_onetime + earnings_subscribtions

        return {
            "earnings_total": earnings_total,
            "earnings_onetime": earnings_onetime,
            "earnings_subscribtions": earnings_subscribtions
        }