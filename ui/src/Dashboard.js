import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import DashboardTable from './DashboardTable'
import Disclaimer from './Disclaimer';
import Footer from './Footer'
import Grid from '@mui/material/Grid';
import { useEffect, useState } from 'react';
import { FETCH_PATH } from './environment'

function Dashboard() {
  const [isLoggedIn, setLogin] = useState(false);
  const [models, setModels] = useState([]);
  const [user, setUser] = useState(null)

  useEffect(() => {
    fetch(`${FETCH_PATH}/api/me`)
      .then(response => response.json())
      .then((data) => {
        if (data["redirect"] !== undefined) {
          window.location.href = data.redirect;
        }
        else {
          setLogin(true);
          setUser(data["user_data"]);
        }
      })
  }, []);

  function getModels() {
    fetch(`${FETCH_PATH}/api/models`)
      .then(response => response.json())
      .then((data) => {
        setModels(data.models);
      })
  }


  useEffect(() => {
    getModels();
  });

  if (isLoggedIn) {
    return (
      <div>
        <Grid
          container
          spacing={0}
          direction="column"
          alignItems="center"
          justifyContent="space-between"
          style={{ minHeight: '100vh', gap: '15px', backgroundImage: 'url(' + require('./background.jpg') + ')' }}
        >
          <ResponsiveAppBar user={user} />
          <Disclaimer />
          <Dz />
          <DashboardTable models={models} />
          <Footer />
        </Grid>
      </div>
    );
  }
}

export default Dashboard;
