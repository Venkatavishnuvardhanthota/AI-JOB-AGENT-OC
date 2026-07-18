import { Routes, Route } from 'react-router-dom'

function HomePage() {
  return (
    <div>
      <h1>AI Job Application Agent</h1>
      <p>Welcome to the AI Job Application Agent.</p>
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
    </Routes>
  )
}

export default App
