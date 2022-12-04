import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
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
      <ResponsiveAppBar user={user}/>
      <h1>Index</h1>
      <Dz />
    </div>
    );
  }
}

export default App;
