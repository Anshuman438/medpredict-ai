function AnalyzingLoader() {
  return (
    <div className="ai-scanner-container">
      <div className="scanner-circle">
        <div className="scan-line"></div>
      </div>
      <div className="scanning-text">
        <span>AI Engine Analyzing Symptoms...</span>
        <div className="progress-dots">
          <div className="dot"></div>
          <div className="dot"></div>
          <div className="dot"></div>
        </div>
      </div>
    </div>
  )
}

export default AnalyzingLoader