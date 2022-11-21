import logo from './logo.svg';
import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import DashboardTable from './DashboardTable'
import {useEffect, useState,useLayoutEffect} from 'react';


function Dashboard() {

  const [models, setModels] = useState([]);
  
  useLayoutEffect(() => {
    fetch('/api/login')
      .then(response => response.json())
      .then((data) => {
        console.log(data.redirect);
        window.location.href = data.redirect;
      })
  },[]);

  return (
    <div>

      <ResponsiveAppBar/>
      <h1>Dashboard</h1>
      <Dz />
      <DashboardTable models={models}/>
      
    </div>
  );
}

export default Dashboard;
