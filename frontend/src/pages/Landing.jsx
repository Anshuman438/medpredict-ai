import { useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthContext } from '../context/AuthContext'

function Landing() {
  const { user } = useContext(AuthContext)
  const navigate = useNavigate()

  return (
    <div className="landing-container">

      <div className="hero-section">
        <h1>MedPredict AI</h1>
        <p>
          Intelligent Symptom & Wellness Platform powered by Machine Learning.
          Get real-time health insights with AI-backed recommendations.
        </p>

        <div className="hero-buttons">
          {!user ? (
            <>
              <button
                className="primary-btn"
                onClick={() => navigate('/register')}
              >
                Get Started
              </button>

              <button
                className="secondary-btn"
                onClick={() => navigate('/login')}
              >
                Login
              </button>
            </>
          ) : (
            <button
              className="primary-btn"
              onClick={() => navigate('/dashboard')}
            >
              Go to Dashboard
            </button>
          )}
        </div>
      </div>

      <div className="features-section">
        <div className="feature-card">
          <h3>AI Symptom Analysis</h3>
          <p>ML-powered health risk predictions with confidence scoring.</p>
        </div>

        <div className="feature-card">
          <h3>Personalized Recommendations</h3>
          <p>Exercise, diet, and lifestyle advice tailored to your risk level.</p>
        </div>

        <div className="feature-card">
          <h3>Health Analytics Dashboard</h3>
          <p>Track trends, risk distribution, and progress over time.</p>
        </div>
      </div>

    </div>
  )
}

export default Landing