import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import {useEffect, useState} from 'react';


function App() {
  const [isLoggedIn, setLogin] = useState(false);
  
  useEffect(() => {
    fetch('/api/me')
      .then(response => response.json())
      .then((data) => {
        if(data["redirect"] !== undefined){
          window.location.href = data.redirect;
        }  
        else{
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
