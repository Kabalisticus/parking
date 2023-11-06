from fastapi.testclient import TestClient
from app import app
import pytest
import random
from datetime import datetime, timedelta

client = TestClient(app)

def get_random_plate_nr():
    return "ABC-12" + str(random.randrange(100,999))

def get_random_entry_date():
    start_date = datetime.strptime('2023-01-01', '%Y-%m-%d')
    mid_date = datetime.strptime('2023-03-31', '%Y-%m-%d')
    end_date = datetime.strptime('2023-12-31', '%Y-%m-%d')

    delta_start = mid_date - start_date

    random_start_days = random.randint(0,delta_start.days)
    random_start_date = start_date + timedelta(days=random_start_days)

    delta_end = end_date - random_start_date

    random_end_days = random.randint(0,delta_end.days)
    random_end_date = (random_start_date + timedelta(days=random_end_days)).strftime('%Y-%m-%d')

    random_start_date = random_start_date.strftime('%Y-%m-%d')

    return random_start_date, random_end_date

def test_parking_happy_path():
    # generate input data needed:plate number, entry date, exit date
    random_plate_number = get_random_plate_nr()
    random_entry_date,random_exit_date = get_random_entry_date()


    # do we have enough parking spots
    response_initial_parking_spots = client.get("/stats/free-spots")
    assert response_initial_parking_spots.status_code == 200
    initial_free_spots_json = response_initial_parking_spots.json()
    assert 'free_spots' in initial_free_spots_json
    assert initial_free_spots_json['free_spots'] > 0
    
    # entry test
    entry_json = {
        "plate_number": random_plate_number,
        "date_entry": random_entry_date
    }
    response_entry = client.post("/register/enter", json= entry_json)
    assert response_entry.status_code == 200

    # check if parking spots number decreased
    response_mid_parking_spots = client.get("/stats/free-spots")
    assert response_mid_parking_spots.status_code == 200
    mid_parking_spots_json = response_mid_parking_spots.json()
    assert 'free_spots' in mid_parking_spots_json
    assert mid_parking_spots_json['free_spots'] == initial_free_spots_json['free_spots'] - 1

    #exit test
    exit_json = {
        "plate_number": random_plate_number,
        "exit_date": random_exit_date
    }

    response_exit = client.post("register/exit", json = exit_json)
    assert response_exit.status_code == 200
    
    # payment test
    payment_json = {
    "ticket_number": response_exit.json()["ticket_number"],
    "payment_value": response_exit.json()["pay_amount"],
    "date_payment": random_exit_date
    }

    response_payment_onetime = client.post("payments/onetime" ,json = payment_json)
    assert response_payment_onetime.status_code == 200
    assert response_payment_onetime.json()["message"] == "You're free to go, Please visit us again"

    # check if parking spots number increased
    response_end_parking_spots = client.get("/stats/free-spots")
    assert response_end_parking_spots.status_code == 200
    end_parking_spots_json = response_end_parking_spots.json()
    assert 'free_spots' in end_parking_spots_json
    assert end_parking_spots_json['free_spots'] == initial_free_spots_json['free_spots']

    # #clear database
    response_clear_database = client.delete("/debug/clear-database")
    assert response_clear_database.status_code == 200


