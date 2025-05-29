import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SignInPage from './pages/SignInPage.jsx';
import SignUpPage from './pages/SignUpPage.jsx';
import ChatPage from './pages/ChatPage.jsx';
import DashboardLayout from './pages/DashboardLayout.jsx';
import MainGrid from './components/dashboard/MainGrid.jsx';
import PDFViewer from './pages/PDFViewer.jsx';
import AdminUserManagement from './components/dashboard/adminpage.jsx';

function App() {
  return (
    <Router>
      <Routes>
        {/* Routes that do not use the AppBar */}
        <Route path="/" element={<SignInPage />} />
        <Route path="/signin" element={<SignInPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        
        {/* Commented out OfficesPage since it's not imported */}
        {/* <Route path="/offices" element={<OfficesPage />} /> */}

        {/* Routes that share the common layout */}
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/pdf/:pdfFilename/*" element={<PDFViewer />} />
        <Route path="/dashboard/*" element={<DashboardLayout />}>
          <Route index element={<MainGrid />} />
          <Route path="admin" element={<AdminUserManagement />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
