import NavBar from "./components/NavBar";
import RegisterEntry from "./components/RegisterEntry";
import RegisterExit from "./components/RegisterExit";
import RegisterSubscription from "./components/RegisterSubscription";


function App() {

  return (

    <div>
      <NavBar/>
      <RegisterSubscription></RegisterSubscription>
      <RegisterEntry></RegisterEntry>
      <RegisterExit></RegisterExit>
    </div>
  );
}

export default App;

