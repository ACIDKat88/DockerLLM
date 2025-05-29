// src/components/Layout.jsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import AppAppBar from './shared-theme/AppAppBar.jsx';

const Layout = () => {
  return (
    <>
      <AppAppBar />
      <main style={{ paddingTop: '80px' }}>
        {/* Adjust the padding if needed to prevent content from being hidden under the AppBar */}
        <Outlet />
      </main>
    </>
  );
};

export default Layout;
