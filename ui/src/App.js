import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import {useEffect, useState} from 'react';
import { FETCH_PATH } from './environment'

console.log("Test env variable ", FETCH_PATH, {FETCH_PATH})

function App() {
  const [isLoggedIn, setLogin] = useState(false);
  
  useEffect(() => {
    fetch(`${FETCH_PATH}/api/me`)
      .then(response => response.json())
      .then((data) => {
        if(data["redirect"] !== undefined){
          window.location.href = data.redirect;
        }  
        else{
          console.log(data)
          setLogin(true)
        }
      })
  },[]);

if(isLoggedIn){
  return (
    <div>
      <ResponsiveAppBar/>
      <h1>Index</h1>
      <Dz />
    </div>
    );
  }
}

export default App;
