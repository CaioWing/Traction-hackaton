import React from 'react';
import logo from './logo.svg';
import './App.css';
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import ServiceOrder from './pages/ServiceOrder';
import ServicesList from './pages/ServicesList';

function App() {
  return (
    <>
      <Routes>
        <Route path='/' element={<Home />} />
        <Route path='/service/:id' element={<ServiceOrder />} />
        <Route path='/services' element={<ServicesList />} />
      </Routes>
    </>
  );
}

export default App;
