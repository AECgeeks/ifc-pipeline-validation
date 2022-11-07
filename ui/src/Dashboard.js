import logo from './logo.svg';
import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'
import {useEffect, useState} from 'react';

function Dashboard() {
  return (
    <div className="App">
      <ResponsiveAppBar/>
      <Dz/>
    </div>
  );
}

export default Dashboard;
