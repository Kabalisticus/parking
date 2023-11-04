import React from "react";
import { ChangeEvent, FormEvent, useState } from "react";

function PaymentSubscription() {
  // State hook to manage form data
  const [formData, setFormData] = useState({
    subscription_ID: "",
    payment_value: "",
    date_payment: "",
  });

  // Function to handle input changes and update form data
  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  // Function to handle form submission
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    try {
      // Log the JSON data being sent to the backend
      console.log("Sending JSON data: ", JSON.stringify(formData));

      // Send a POST request to the backend
      const response = await fetch(
        "http://localhost:8000/payments/subscription",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(formData), // Convert form data to JSON
        }
      );

      // Check if the response is successful
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      // Parse the JSON response from the server
      const data = await response.json();
      console.log(data); // Log the response data
    } catch (error) {
      console.error("Error:", error); // Log any errors that occur during the process
    }
  };

  // JSX content for the form
  return (
    <div>
      <br></br>
      <br></br>
      <h2>Subscription payment</h2>
      <br></br>
      <form onSubmit={handleSubmit}>
        {/* Input field for plate number */}
        <div className="form-floating mb-3">
          <input
            type="number"
            name="subscription_ID"
            value={formData.subscription_ID}
            onChange={handleInputChange}
            className="form-control"
            id="floatingInput"
            placeholder="44"
          />
          <label htmlFor="floatingInput">Subscription ID</label>
        </div>

        {/* Input field for subscription start date */}
        <div className="form-floating mb-3">
          <input
            type="text"
            name="payment_value"
            value={formData.payment_value}
            onChange={handleInputChange}
            pattern="^\d+(,\d{1,2})?$"
            className="form-control"
            id="floatingInput"
            placeholder="Subscription payment value"
          />
          <label htmlFor="floatingInput">Subscription payment value</label>
        </div>

        {/* Input field for subscription end date */}
        <div className="form-floating mb-3">
          <input
            type="date"
            name="date_payment"
            value={formData.date_payment}
            onChange={handleInputChange}
            className="form-control"
            id="floatingInput"
            placeholder="Subscription payment date"
          />
          <label htmlFor="floatingInput">Subscription payment date</label>
        </div>

        {/* Submit button for the form */}
        <button type="submit">Proceed with payment</button>
      </form>
    </div>
  );
}

export default PaymentSubscription;
