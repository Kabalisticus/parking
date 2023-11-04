function NavBar() {
  return (
    <nav className="navbar navbar-expand-lg bg-body-tertiary">
      <div className="container-fluid">
        <a className="navbar-brand" href="#">
          <img
            src="../src/assets/parking.png"
            alt="Logo"
            width="50"
            height="40"
            className="d-inline-block align-text-middle me-2"
          />
          <span className="fs-2">PARKING</span>
        </a>

        <div className="collapse navbar-collapse" id="navbarNavAltMarkup">
          <div className="navbar-nav"></div>
        </div>
      </div>
    </nav>
  );
}

export default NavBar;
