from datetime import datetime
from fastapi import FastAPI
import asyncpg
from models import Payment_status, Vehicle, Entry_exit_register, Subscribtion, Payments

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
async def zarejestruj_abonament(numer_tablicy: str, date_start: str, date_end: str):
    async with app.state.pool.acquire() as connection:

        # Convert to date format
        data_rozpoczecia = datetime.strptime(date_start, "%Y-%m-%d").date()
        data_zakonczenia = datetime.strptime(date_end, "%Y-%m-%d").date()

        # Check if the vehicle is already in database:
        pojazd_istnieje_zapytanie = "SELECT 1 FROM pojazdy WHERE numer_rejestracyjny = $1"
        pojazd_istnieje = await connection.fetchval(pojazd_istnieje_zapytanie, numer_tablicy)
        # If vevicle is not present
        if not pojazd_istnieje:

            # Update the sequence counter for pojazdy
            await connection.execute("SELECT setval('pojazdy_numer_pojazdu_seq', (SELECT max(numer_pojazdu) FROM pojazdy))")

            # Add new entry to the pojazdy database
            
            pojazdy_wstaw_zapytanie = """

            INSERT INTO pojazdy (numer_rejestracyjny) VALUES ($1)"""


            await connection.execute(pojazdy_wstaw_zapytanie, numer_tablicy)
            
        # Update sequence counter for rejestr_wjazdu_wyjazdu
        await connection.execute("SELECT setval('rejestr_wjazdu_wyjazdu_numer_wydruku_seq', (SELECT max(numer_wydruku) FROM rejestr_wjazdu_wyjazdu))")
        # Add new entry to the abonamenty table
        abonamenty_wstaw_zapytanie = """
            INSERT INTO abonamenty (numer_rejestracyjny, data_rozpoczecia, data_zakonczenia)
            VALUES ($1, $2, $3)
        """
        await connection.execute(abonamenty_wstaw_zapytanie, numer_tablicy, data_rozpoczecia, data_zakonczenia)

        return {"message": "Nowy abonament zarejestrowano pomyślnie"}

# Register a new entry on the parking
@app.post("/register/enter")

async def zarejestruj_wjazd (numer_tablicy: str, date_entry: str):
    async with app.state.pool.acquire() as connection:
        
        czas_wjazdu = datetime.strptime(date_entry, "%Y-%m-%d").date()

        # Check if the vehicle is already in the database
        pojazd_istnieje_zapytanie = "SELECT 1 FROM pojazdy WHERE numer_rejestracyjny = $1"
        pojazd_istnieje = await connection.fetchval(pojazd_istnieje_zapytanie, numer_tablicy)
        # If vehicle not present
        if not pojazd_istnieje:

        # Update the sequence counter for Pojazdy table
            await connection.execute("SELECT setval('pojazdy_numer_pojazdu_seq', (SELECT max(numer_pojazdu) FROM pojazdy))")

        # Add new entry to Pojazdy table
            pojazdy_wstaw_zapytanie = """

            INSERT INTO pojazdy (numer_rejestracyjny) VALUES ($1)"""

            await connection.execute(pojazdy_wstaw_zapytanie, numer_tablicy)
            
            #Update sequence counter for rejestr_wjazdu_wyjazdu table 

            await connection.execute("SELECT setval('rejestr_wjazdu_wyjazdu_numer_wydruku_seq', (SELECT max(numer_wydruku) FROM rejestr_wjazdu_wyjazdu))")


        # Add new entry to rejestr wjazdu wyjazdu table
        rejestr_wjazdu_wyjazdu_zapytanie = """ 
            INSERT INTO rejestr_wjazdu_wyjazdu (numer_rejestracyjny, czas_wjazdu, czas_wyjazdu, kwota, status_platnosci)
            VALUES ($1, $2, NULL, 0, 'Oczekuje')
        """
        await connection.execute(rejestr_wjazdu_wyjazdu_zapytanie, numer_tablicy, czas_wjazdu)

        return {"message": "Nowy wjazd zarejestrowano pomyślnie"}

# Register the exit of the vehicle    
@app.post("/register/exit")
async def zarejestruj_wyjazd (
    numer_tablicy: str, data_wyjazdu: str, data_platnosci: str, taryfa: int):

    async with app.state.pool.acquire() as connection:

    # Translate variables
        NumerTablicy = numer_tablicy
        Taryfa = taryfa

        # STR to DATE conversion
        DataWyjazdu = datetime.strptime(data_wyjazdu, "%Y-%m-%d").date()
        DataPlatnosci = datetime.strptime(data_platnosci, "%Y-%m-%d").date()
    
    #Assign values fof the variables

        # Subscribtion end date
        data_zakonczenia_zapytanie = """
        SELECT a.data_zakonczenia
        FROM abonamenty a
        WHERE a.numer_rejestracyjny = $1 AND a.data_zakonczenia IS NOT NULL
        """
        DataZakonczeniaAbonamentu = await connection.fetchval(
            data_zakonczenia_zapytanie, NumerTablicy
        )

        # Subscribtion start date
        data_rozpoczecia_zapytanie = """
        SELECT a.data_rozpoczecia
        FROM abonamenty a
        WHERE a.numer_rejestracyjny = $1 AND a.data_rozpoczecia IS NOT NULL
        """
        DataRozpoczeciaAbonamentu = await connection.fetchval(
            data_rozpoczecia_zapytanie, NumerTablicy
        )


        # Entry on the parking date
        data_wjazdu_zapytanie = """
        SELECT rww.czas_wjazdu
        FROM rejestr_wjazdu_wyjazdu rww
        WHERE rww.numer_rejestracyjny = $1 AND rww.czas_wyjazdu IS NULL
        """
        DataWjazdu = await connection.fetchval(data_wjazdu_zapytanie, NumerTablicy)


        # Ticket number 
        numer_wydruku_zapytanie = """
        SELECT rww.numer_wydruku
        FROM rejestr_wjazdu_wyjazdu rww
        WHERE rww.numer_rejestracyjny = $1 AND rww.czas_wyjazdu IS NULL
        """
        NumerWydruku = await connection.fetchval(
            numer_wydruku_zapytanie, NumerTablicy
        )

# Check for the subscription status on entry and exit
 
        subscription_status_zapytanie = """
        SELECT
            CASE
                WHEN rww.czas_wjazdu BETWEEN a.data_rozpoczecia AND a.data_zakonczenia THEN TRUE
                ELSE FALSE
            END,
            CASE
                WHEN a.data_zakonczenia >= $2 THEN TRUE
                ELSE FALSE
            END
        FROM rejestr_wjazdu_wyjazdu rww
        JOIN pojazdy p ON rww.numer_rejestracyjny = p.numer_rejestracyjny
        JOIN abonamenty a ON p.numer_rejestracyjny = a.numer_rejestracyjny
        WHERE p.numer_rejestracyjny = $1 AND rww.czas_wyjazdu IS NULL
        """
        AbonamentAktywnyWjazd, AbonamentAktywnyWyjazd = await connection.fetchrow(
            subscription_status_zapytanie, NumerTablicy, DataWyjazdu
        )

        # Cases depending on subscription status
        if AbonamentAktywnyWjazd and AbonamentAktywnyWyjazd:
            KwotaDoZaplaty = 0
        elif AbonamentAktywnyWjazd and not AbonamentAktywnyWyjazd:
            KwotaDoZaplaty = (DataZakonczeniaAbonamentu - DataWjazdu).days * Taryfa
        elif not AbonamentAktywnyWjazd and not AbonamentAktywnyWyjazd:
            KwotaDoZaplaty = (DataWyjazdu - DataWjazdu).days * Taryfa
        else:
            KwotaDoZaplaty = (DataRozpoczeciaAbonamentu - DataWjazdu).days * Taryfa

        # Update the 'rejestr_wjazdu_wyjazdu' table
        update_zapytanie = """
        UPDATE rejestr_wjazdu_wyjazdu
        SET 
            czas_wyjazdu = $1,
            status_platnosci = 'Oczekuje'
        WHERE numer_rejestracyjny = $2 AND czas_wyjazdu IS NULL
        """
        await connection.execute(update_zapytanie, DataWyjazdu, NumerTablicy)

        # Add an entry to 'platnosci_jednorazowe' if it doesn't exist
        sprawdz_platnosc_zapytanie = """
        SELECT 1 FROM platnosci_jednorazowe WHERE numer_wydruku = $1
        """
        platnosc_istnieje = await connection.fetchval(sprawdz_platnosc_zapytanie, NumerWydruku)


        if not platnosc_istnieje:
            wstaw_platnosc_zapytanie = """
            INSERT INTO platnosci_jednorazowe (numer_wydruku, kwota, status_platnosci, data_platnosci)
            VALUES ($1, $2, 'Zakonczono', $3)
            """
            await connection.execute(
                wstaw_platnosc_zapytanie, NumerWydruku, KwotaDoZaplaty, DataPlatnosci
            )

            # Commit the transaction
            await connection.commit()

            return {"message": "Payment registered successfully"}    

# Calculate the number of free spots on the parking
@app.get("/stats/free-spots")
async def wolne_miejsca():
    async with app.state.pool.acquire() as connection:

# Assign values to the variables

        #calculate all of the parked vehicles
        zaparkowane_wszystkie_zapytanie = """
        SELECT COUNT(*)
        FROM rejestr_wjazdu_wyjazdu
        WHERE czas_wyjazdu IS NULL;
        """   
        zaparkowane_wszystkie = await connection.fetchval(zaparkowane_wszystkie_zapytanie)

        #calculate number of the parked vehicles with active subscribtion
        zaparkowane_abonament_zapytanie = """
        SELECT COUNT(*)
        FROM rejestr_wjazdu_wyjazdu rww
        JOIN pojazdy p ON rww.numer_rejestracyjny = p.numer_rejestracyjny
        JOIN abonamenty a ON p.numer_rejestracyjny = a.numer_rejestracyjny
        WHERE rww.czas_wyjazdu IS NULL
        AND CURRENT_DATE BETWEEN a.data_rozpoczecia AND a.data_zakonczenia;
        """
        
        zaparkowane_abonament = await connection.fetchval(zaparkowane_abonament_zapytanie)
        
        #calculate number of all vehicles with active subscribtion
        wszystkie_abonament_zapytanie = """
        SELECT COUNT(*)
        FROM pojazdy p
        JOIN abonamenty a ON p.numer_rejestracyjny = a.numer_rejestracyjny
        WHERE CURRENT_DATE BETWEEN a.data_rozpoczecia AND a.data_zakonczenia;
        """    
        wszystkie_abonament = await connection.fetchval(wszystkie_abonament_zapytanie)

        #calculate number of free spots 
        wolne_miejsca = 50 - zaparkowane_wszystkie + zaparkowane_abonament - wszystkie_abonament
        return {"message": f"Liczba wolnych miejsc wynosi: {wolne_miejsca}"}
    
    
#Calculate revenues from subscribtions and single entries 
@app.get("/stats/financial")
async def get_platnosci(date_start: str, date_end: str):
    async with app.state.pool.acquire() as connection:

        # Convert str to date
        data_poczatkowa = datetime.strptime(date_start, "%Y-%m-%d").date()
        data_koncowa = datetime.strptime(date_end, "%Y-%m-%d").date()
        
#Assign values to the variables

        # Calculate the revenues from single payments
        zarobki_jednorazowe_zapytanie = """
            SELECT COALESCE(SUM(kwota), 0)
            FROM platnosci_jednorazowe 
            WHERE data_platnosci BETWEEN $1 AND $2
        """
        zarobki_jednorazowe = await connection.fetchval(zarobki_jednorazowe_zapytanie, data_poczatkowa, data_koncowa)

        #Calculate the revenues from subscribtions
        zarobki_abonament_zapytanie = """
            SELECT COALESCE(SUM(EXTRACT(YEAR FROM age(data_zakonczenia, data_rozpoczecia)) * 12 + EXTRACT(MONTH FROM age(data_zakonczenia, data_rozpoczecia))) * 100, 0)
            FROM abonamenty
            WHERE data_rozpoczecia >= $1 AND data_zakonczenia <= $2
        """ 
        zarobki_abonament = await connection.fetchval(zarobki_abonament_zapytanie, data_poczatkowa, data_koncowa)

        # Calculate the sum of the revenues 
        suma_zarobkow = zarobki_jednorazowe + zarobki_abonament

        print("Zarobiono łącznie:", suma_zarobkow)
        print("Zarobiono jednorazowo:", zarobki_jednorazowe)
        print("Zarobiono na abonamentach:", zarobki_abonament)

        return {
            "suma_zarobkow": suma_zarobkow,
            "zarobki_jednorazowe": zarobki_jednorazowe,
            "zarobki_abonament": zarobki_abonament
        }
    
