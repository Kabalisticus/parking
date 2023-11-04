import { ChangeEvent, FormEvent, useState } from "react";

const GetEarnings = () => {
  // State to manage form data
  const [formData, setFormData] = useState({
    start_date: "",
    end_date: "",
  });

  // State to manage earnings data
  const [earnings, setEarnings] = useState({
    earnings_total: 0,
    earnings_onetime: 0,
    earnings_subscriptions: 0,
  });

  // Function to handle input changes
  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  // Function to handle form submission
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      // Construct the URL with form data
      const url = `http://localhost:8000/stats/financial?start_date=${formData.start_date}&end_date=${formData.end_date}`;
      // Send a GET request to the server
      const response = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }
      // Parse the JSON response and update earnings data
      const data = await response.json();
      setEarnings(data);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div>
      <br />
      <br />
      <h2>Get earnings</h2>

      <form onSubmit={handleSubmit}>
        {/* Input field for start date */}
        <div className="form-floating mb-3">
          <input
            type="date"
            name="start_date"
            value={formData.start_date}
            onChange={handleInputChange}
            className="form-control"
            id="floatingInput"
            placeholder="44"
          />
          <label htmlFor="floatingInput">Start date</label>
        </div>

        {/* Input field for end date */}
        <div className="form-floating mb-3">
          <input
            type="date"
            name="end_date"
            value={formData.end_date}
            onChange={handleInputChange}
            className="form-control"
            id="floatingInput"
            placeholder="End date"
          />
          <label htmlFor="floatingInput">End date</label>
        </div>

        {/* Submit button for the form */}
        <button type="submit">Check earnings</button>
      </form>

      {/* Display earnings data */}
      <div>
        <br />
        <h5>Earnings Total: {earnings.earnings_total}</h5>
        <h5>Earnings One-Time: {earnings.earnings_onetime}</h5>
        <h5>Earnings Subscriptions: {earnings.earnings_subscriptions}</h5>
      </div>
    </div>
  );
};

export default GetEarnings;
