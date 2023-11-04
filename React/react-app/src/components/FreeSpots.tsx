import { useState } from "react";

const FreeSpots = () => {
  const [freeSpots, setFreeSpots] = useState(null);

  const fetchData = async () => {
    try {
      const response = await fetch("http://localhost:8000/stats/free-spots");
      const data = await response.json();
      setFreeSpots(data.free_spots);
    } catch (error) {
      console.error("Error fetching data: ", error);
    }
  };

  return (
    <div>
      <br />
      <br />
      <h2>Free spots</h2>
      {freeSpots !== null ? (
        <div
          style={{
            display: "inline-block",
            backgroundColor: "lightblue",
            padding: "10px",
          }}
        >
          <p style={{ color: "black", margin: 0 }}>
            Number of free spots: {freeSpots}
          </p>
        </div>
      ) : (
        <p style={{ color: "black", margin: 0 }}>Loading...</p>
      )}
      <br />
      <br />
      <button onClick={fetchData}>Get Free Spots</button>
    </div>
  );
};

export default FreeSpots;
