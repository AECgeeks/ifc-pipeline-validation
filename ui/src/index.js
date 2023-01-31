import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import Dashboard from './Dashboard';
import Callback from './Callback';
import Logout from './Logout';
import Report from './Report';
import reportWebVitals from './reportWebVitals';
import { BrowserRouter, Routes, Route } from "react-router-dom";

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  // <React.StrictMode>

  <BrowserRouter>
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="sandbox/:commitId/" element={<App />} />

      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="sandbox/dashboard/:commitId" element={<Dashboard />} />

      <Route path="/report/:modelCode" element={<Report />} />
      <Route path="/sandbox/report/:commitId/:modelCode" element={<Report />} />

      <Route path="/callback" element={<Callback />} />
      <Route path="/logout" element={<Logout />} />
    </Routes>
  </BrowserRouter>



  // </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
