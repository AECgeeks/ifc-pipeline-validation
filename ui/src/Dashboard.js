import logo from './logo.svg';
import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import DashboardTable from './DashboardTable'
import {useEffect, useState} from 'react';


function Dashboard() {

  const [models, setModels] = useState([]);
  
  useEffect(() => {
    fetch('/api/models')
      .then(response => response.json())
      .then((data) => {
        setModels(data.models);
      })
  });

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
