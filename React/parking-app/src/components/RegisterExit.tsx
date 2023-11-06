import { ChangeEvent, FormEvent, useState } from "react";

function RegisterExit() {
  // State hook to manage form data
  const [formData, setFormData] = useState({
    plate_number: "",
    exit_date: "",
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
      const response = await fetch("http://localhost:8000/register/exit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData), // Convert form data to JSON
      });

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
      <h2>Register new exit</h2>
      <br></br>
      <form onSubmit={handleSubmit}>
        {/* Input field for plate number */}
        <div className="form-floating mb-3">
          <input
            type="text"
            name="plate_number"
            value={formData.plate_number}
            onChange={handleInputChange}
            className="form-control"
            id="floatingInput"
            placeholder="POK-HN23P"
          />
          <label htmlFor="floatingInput">Plate number</label>
        </div>

        {/* Input field for subscription start date */}
        <div className="form-floating mb-3">
          <input
            type="date"
            name="exit_date"
            value={formData.exit_date}
            onChange={handleInputChange}
            className="form-control"
            id="floatingInput"
            placeholder="Exit date"
          />
          <label htmlFor="floatingInput">Exit date</label>
        </div>

        {/* Submit button for the form */}
        <button type="submit">Register</button>
      </form>
    </div>
  );
}

export default RegisterExit;