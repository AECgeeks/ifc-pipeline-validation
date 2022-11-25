import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import DashboardTable from './DashboardTable'
import {useEffect, useState} from 'react';


function Dashboard() {
  const [isLoggedIn, setLogin] = useState(false);
  const [models, setModels] = useState([]);
  
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
      <h1>Dashboard</h1>
      <Dz />
      <DashboardTable models={models}/>
    </div>
    );
  }
}

export default Dashboard;
