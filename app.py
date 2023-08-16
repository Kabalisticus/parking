from datetime import datetime
from fastapi import FastAPI
import asyncpg

app = FastAPI()

# Konfiguracja bazy danych
DATABASE_URL = "postgresql://parking:123test@localhost:5432/parking"

@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(DATABASE_URL)

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()


@app.get("/stats/financial")
#Definicja funkcji asynchronicznej o parametrach date_start, date_end
async def get_platnosci(date_start: str, date_end: str):
    async with app.state.pool.acquire() as connection:
        # konwersja formatu z STR do DATE
        data_poczatkowa = datetime.strptime(date_start, "%Y-%m-%d").date()
        data_koncowa = datetime.strptime(date_end, "%Y-%m-%d").date()
        # przypisanie wartości do zapytania, suma kwot z platnosci w zadanym przedziale czasowym
        zarobki_jednorazowe_zapytanie = """
            SELECT COALESCE(SUM(kwota), 0)
            FROM platnosci_jednorazowe 
            WHERE data_platnosci BETWEEN $1 AND $2
        """
        # przypisz wartość do zmiennej. Pobierz wartość w oparciu o zmienne (query, arg1, arg2) 
        zarobki_jednorazowe = await connection.fetchval(zarobki_jednorazowe_zapytanie, data_poczatkowa, data_koncowa)

        #przypisanie wartości do zapytania, suma kwot z abonamentów
        zarobki_abonament_zapytanie = """
            SELECT COALESCE(SUM(EXTRACT(YEAR FROM age(data_zakonczenia, data_rozpoczecia)) * 12 + EXTRACT(MONTH FROM age(data_zakonczenia, data_rozpoczecia))) * 100, 0)
            FROM abonamenty
            WHERE data_rozpoczecia >= $1 AND data_zakonczenia <= $2
        """
        #przypisanie wartości do zmiennej 
        zarobki_abonament = await connection.fetchval(zarobki_abonament_zapytanie, data_poczatkowa, data_koncowa)


        suma_zarobkow = zarobki_jednorazowe + zarobki_abonament

        print("Zarobiono łącznie:", suma_zarobkow)
        print("Zarobiono jednorazowo:", zarobki_jednorazowe)
        print("Zarobiono na abonamentach:", zarobki_abonament)

        return {
            "suma_zarobkow": suma_zarobkow,
            "zarobki_jednorazowe": zarobki_jednorazowe,
            "zarobki_abonament": zarobki_abonament
        }
    


@app.post("/payments/subscribe")
#Definicja funkcj asynchronicznej
async def zarejestruj_abonament(numer_tablicy: str, date_start: str, date_end: str):
    async with app.state.pool.acquire() as connection:

        # Konwersja formatu z STR do DATE
        data_rozpoczecia = datetime.strptime(date_start, "%Y-%m-%d").date()
        data_zakonczenia = datetime.strptime(date_end, "%Y-%m-%d").date()

        # Sprawdzenie czy pojazd znajduje się w bazie:
        pojazd_istnieje_zapytanie = "SELECT 1 FROM pojazdy WHERE numer_rejestracyjny = $1"
        pojazd_istnieje = await connection.fetchval(pojazd_istnieje_zapytanie, numer_tablicy)
        # Jeśli pojazdu nie ma w bazie
        if not pojazd_istnieje:

            # Zaktualizuj sequence counter
            await connection.execute("SELECT setval('pojazdy_numer_pojazdu_seq', (SELECT max(numer_pojazdu) FROM pojazdy))")

            # Wstaw nowy wpis do tabeli pojazdy
            
            pojazdy_wstaw_zapytanie = """

            INSERT INTO pojazdy (numer_rejestracyjny) VALUES ($1)"""


            await connection.execute(pojazdy_wstaw_zapytanie, numer_tablicy)

        # Zaktualizuj sequence counter
        await connection.execute("SELECT setval('rejestr_wjazdu_wyjazdu_numer_wydruku_seq', (SELECT max(numer_wydruku) FROM rejestr_wjazdu_wyjazdu))")
        # Nowy wpis do tabeli abonamenty
        abonamenty_wstaw_zapytanie = """
            INSERT INTO abonamenty (numer_rejestracyjny, data_rozpoczecia, data_zakonczenia)
            VALUES ($1, $2, $3)
        """
        await connection.execute(abonamenty_wstaw_zapytanie, numer_tablicy, data_rozpoczecia, data_zakonczenia)

        return {"message": "Nowy abonament zarejestrowano pomyślnie"}


@app.post("/register/enter")
#Definicja funkcj asynchronicznej
async def zarejestruj_wjazd (numer_tablicy: str, date_start: str):
    async with app.state.pool.acquire() as connection:

        # Konwersja formatu z STR do DATE
        data_rozpoczecia = datetime.strptime(date_start, "%Y-%m-%d").date()

        # Sprawdzenie czy pojazd znajduje się w bazie:
        pojazd_istnieje_zapytanie = "SELECT 1 FROM pojazdy WHERE numer_rejestracyjny = $1"
        pojazd_istnieje = await connection.fetchval(pojazd_istnieje_zapytanie, numer_tablicy)
        # Jeśli pojazdu nie ma w bazie
        if not pojazd_istnieje:
        # Zaktualizuj sequence counter
            await connection.execute("SELECT setval('pojazdy_numer_pojazdu_seq', (SELECT max(numer_pojazdu) FROM pojazdy))")

        # Wstaw nowy wpis do tabeli pojazdy
        
            pojazdy_wstaw_zapytanie = """

            INSERT INTO pojazdy (numer_rejestracyjny) VALUES ($1)"""

            await connection.execute(pojazdy_wstaw_zapytanie, numer_tablicy)
            
            #zaktualizuj sequence counter dla RWW

            await connection.execute("SELECT setval('rejestr_wjazdu_wyjazdu_numer_wydruku_seq', (SELECT max(numer_wydruku) FROM rejestr_wjazdu_wyjazdu))")

        # Nowy wpis do tabeli rejestr wjazdu wyjazdy, zacznij od ostatniego numeru kwitu
        rejestr_wjazdu_wyjazdu_zapytanie = """ 
            INSERT INTO rejestr_wjazdu_wyjazdu (numer_rejestracyjny, czas_wjazdu, czas_wyjazdu, kwota, status_platnosci)
            VALUES ($1, $2, NULL, 0, 'Oczekuje')
        """
        await connection.execute(rejestr_wjazdu_wyjazdu_zapytanie, numer_tablicy, data_rozpoczecia)

        return {"message": "Nowy wjazd zarejestrowano pomyślnie"}

@app.get("/stats/free-spots")
#Definicja funkcj asynchronicznej
async def wolne_miejsca():
    async with app.state.pool.acquire() as connection:

        zaparkowane_wszystkie_zapytanie = """
        SELECT COUNT(*)
        FROM rejestr_wjazdu_wyjazdu
        WHERE czas_wyjazdu IS NULL;
        """   
        zaparkowane_wszystkie = await connection.fetchval(zaparkowane_wszystkie_zapytanie)
        
        zaparkowane_abonament_zapytanie = """
        SELECT COUNT(*)
        FROM rejestr_wjazdu_wyjazdu rww
        JOIN pojazdy p ON rww.numer_rejestracyjny = p.numer_rejestracyjny
        JOIN abonamenty a ON p.numer_rejestracyjny = a.numer_rejestracyjny
        WHERE rww.czas_wyjazdu IS NULL
        AND CURRENT_DATE BETWEEN a.data_rozpoczecia AND a.data_zakonczenia;
        """
        
        zaparkowane_abonament = await connection.fetchval(zaparkowane_abonament_zapytanie)
        
        wszystkie_abonament_zapytanie = """
        SELECT COUNT(*)
        FROM pojazdy p
        JOIN abonamenty a ON p.numer_rejestracyjny = a.numer_rejestracyjny
        WHERE CURRENT_DATE BETWEEN a.data_rozpoczecia AND a.data_zakonczenia;
        """    
        wszystkie_abonament = await connection.fetchval(wszystkie_abonament_zapytanie)

        wolne_miejsca = 50 - zaparkowane_wszystkie + zaparkowane_abonament - wszystkie_abonament
        return {"message": f"Liczba wolnych miejsc wynosi: {wolne_miejsca}"}

#         @app.post("/wyjazd_pojazdu")

#         @app.post("/platnosc_jednorazowa")

