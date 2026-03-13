import { Routes, Route } from 'react-router-dom'
import ScorerPage from './pages/ScorerPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ScorerPage />} />
    </Routes>
  )
}
