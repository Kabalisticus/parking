import React from "react";
import FreeSpots from "./components/FreeSpots.tsx";
import GetEarnings from "./components/GetEarnings.tsx";
import NavBar from "./components/NavBar.tsx";
import PaymentOnetime from "./components/PaymentOnetime.tsx";
import PaymentSubscription from "./components/PaymentSubscription.tsx";
import RegisterEntry from "./components/RegisterEntry.tsx";
import RegisterExit from "./components/RegisterExit.tsx";
import RegisterSubscription from "./components/RegisterSubscription.tsx";

function App() {
  return (
    <div>
      <NavBar />
      <RegisterSubscription />
      <RegisterEntry />
      <RegisterExit />
      <PaymentSubscription />
      <PaymentOnetime />
      <FreeSpots />
      <GetEarnings />
    </div>
  );
}

export default App;
