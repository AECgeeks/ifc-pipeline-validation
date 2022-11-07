import logo from './logo.svg';
import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import {useEffect, useState} from 'react';

function Dashboard() {

  useEffect(() => {
    fetch('/models')
      .then(response => response.json())
      .then((response) => {
        console.log("response", response);
      })
  }, []);

  return (
    <div className="App">
      <Dz/>
    </div>
  );
}

export default Dashboard;
