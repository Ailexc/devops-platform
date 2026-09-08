import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import EventList from './pages/EventList'
import EventDetail from './pages/EventDetail'
import DlqPage from './pages/DlqPage'
import EventTypes from './pages/EventTypes'
import TestLab from './pages/TestLab'
import SystemDocs from './pages/SystemDocs'
import DocsDetail from './pages/DocsDetail'
import InterviewHandbook from './pages/InterviewHandbook'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/events" element={<EventList />} />
        <Route path="/events/:id" element={<EventDetail />} />
        <Route path="/dlq" element={<DlqPage />} />
        <Route path="/event-types" element={<EventTypes />} />
        <Route path="/test-lab" element={<TestLab />} />
        <Route path="/docs" element={<SystemDocs />} />
        <Route path="/docs/handbook" element={<InterviewHandbook />} />
        <Route path="/docs/:filename" element={<DocsDetail />} />
      </Route>
    </Routes>
  )
}
