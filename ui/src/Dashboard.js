import logo from './logo.svg';
import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import {useEffect, useState} from 'react';

function Dashboard() {

  useEffect(() => {
    fetch('http://localhost:5000/models')
      .then(response => response.json())
      .then((response) => {
        console.log("response", response);
      })
  }, []);

  return (
    <div>
      <ResponsiveAppBar/>
      <h1>Dashboard</h1>
      <Dz/>
    </div>
  );
}

export default Dashboard;
