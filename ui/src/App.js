import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import Disclaimer from './Disclaimer';
import Footer from './Footer'
import Grid from '@mui/material/Grid';
import {useEffect, useState} from 'react';
import { FETCH_PATH } from './environment'

function App() {
  const [isLoggedIn, setLogin] = useState(false);
  const [user, setUser] = useState(null)
  
  useEffect(() => {
    fetch(`${FETCH_PATH}/api/me`)
      .then(response => response.json())
      .then((data) => {
        if(data["redirect"] !== undefined){
          window.location.href = data.redirect;
        }  
        else{
          console.log(data)
          setLogin(true);
          setUser(data["user_data"]);
        }
      })
  },[]);

if(isLoggedIn){
  return (
    <div>
        <Grid
          container
          spacing={0}
          direction="column"
          alignItems="center"
          justifyContent="space-between"
          style={{ minHeight: '100vh', gap:'15px', backgroundImage: 'url(' + require('./background.jpg') + ')'}}
        >
        <ResponsiveAppBar user={user}/>
        <Disclaimer />
        <Dz />
        <Footer />
      </Grid>
    </div>


    );
  }
}

export default App;
