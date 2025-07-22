import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SignInPage from './pages/SignInPage.jsx';
import SignUpPage from './pages/SignUpPage.jsx';
import HomePage from './pages/HomePage.jsx';
import ChatPage from './pages/ChatPage.jsx';
import DashboardLayout from './pages/DashboardLayout.jsx';
import Dashboard from './pages/Dashboard.jsx';
import MainGrid from './components/dashboard/MainGrid.jsx';
import UserAnalytics from './components/dashboard/UserAnalytics.jsx';
import PDFViewer from './pages/PDFViewer.jsx';


function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SignInPage />} />
        <Route path="/signin" element={<SignInPage />} />
        <Route path="/signup" element={<SignUpPage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/chat" element={<ChatPage />} />
        {/* PDF Viewer route */}
        <Route path="/pdf/:pdfFilename*" element={<PDFViewer />} />
        {/* Dashboard routes nested under /dashboard/* */}
        <Route path="/dashboard/*" element={<DashboardLayout />}>
          <Route index element={<MainGrid />} />
          <Route path="user-analytics" element={<UserAnalytics />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
