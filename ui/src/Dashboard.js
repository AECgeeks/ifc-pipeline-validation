import logo from './logo.svg';
import './App.css';
import Dz from './Dz'
import ResponsiveAppBar from './ResponsiveAppBar'

function Dashboard() {
  return (
    <div className="App">
      <ResponsiveAppBar/>
      <Dz/>
    </div>
  );
}

export default Dashboard;
