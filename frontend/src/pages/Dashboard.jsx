import MainLayout from '../layouts/MainLayout'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart
} from 'recharts'
import { useState, useEffect } from 'react'
import api from '../services/api'

const COLORS = ['#10B981', '#FACC15', '#EF4444'];

function Dashboard() {
  const [predictions, setPredictions] = useState([])
  const [monthlyData, setMonthlyData] = useState([])
  const [riskData, setRiskData] = useState([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const { data } = await api.get('/predictions/my')
        setPredictions(data)
        processAnalytics(data)
      } catch (error) {
        console.error('Failed to fetch predictions')
      }
    }

    fetchData()
  }, [])

  const processAnalytics = (data) => {
    // Monthly aggregation
    const monthMap = {}

    data.forEach(item => {
      const month = new Date(item.createdAt).toLocaleString('default', { month: 'short' })
      monthMap[month] = (monthMap[month] || 0) + 1
    })

    const formattedMonthly = Object.keys(monthMap).map(month => ({
      month,
      checks: monthMap[month]
    }))

    setMonthlyData(formattedMonthly)

    // Risk aggregation
    const riskMap = { Low: 0, Medium: 0, High: 0 }

    data.forEach(item => {
      riskMap[item.risk]++
    })

    const formattedRisk = Object.keys(riskMap).map(key => ({
      name: key,
      value: riskMap[key]
    }))

    setRiskData(formattedRisk)
  }

  const totalChecks = predictions.length
  const highRisk = predictions.filter(p => p.risk === 'High').length

  const conditionCount = {}
  predictions.forEach(p => {
    conditionCount[p.condition] = (conditionCount[p.condition] || 0) + 1
  })

  const mostCommonCondition =
    Object.keys(conditionCount).length > 0
      ? Object.keys(conditionCount).reduce((a, b) =>
          conditionCount[a] > conditionCount[b] ? a : b
        )
      : 'N/A'

  return (
    <MainLayout>
      <div className="dashboard-container">

        <div className="dashboard-header">
          <div className="header-text">
            <h2>Health Intelligence Hub</h2>
            <p>Real-time diagnostic overview and risk trends</p>
          </div>
          <div className="status-pill">
            <span className="pulse"></span> System Active
          </div>
        </div>

        <div className="stats-grid">
          <div className="kpi-card glass-morph">
            <div className="kpi-icon">📊</div>
            <div>
              <h4>Total Analyzed</h4>
              <h2>{totalChecks}</h2>
            </div>
          </div>

          <div className="kpi-card glass-morph">
            <div className="kpi-icon">⚠️</div>
            <div>
              <h4>High Risk Cases</h4>
              <h2 className="risk-high">{highRisk}</h2>
            </div>
          </div>

          <div className="kpi-card glass-morph">
            <div className="kpi-icon">🧬</div>
            <div>
              <h4>Common Condition</h4>
              <h2>{mostCommonCondition}</h2>
            </div>
          </div>

          <div className="kpi-card glass-morph">
            <div className="kpi-icon">📈</div>
            <div>
              <h4>Monthly Growth</h4>
              <h2 className="growth">Auto</h2>
            </div>
          </div>
        </div>

        <div className="analytics-section">
          
          <div className="chart-card glass-morph">
            <h3>Monthly Predictions</h3>

            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={monthlyData}>
                <XAxis dataKey="month" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    borderRadius: '15px',
                    border: 'none',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.1)'
                  }}
                />

                <Line
                  type="monotone"
                  dataKey="checks"
                  stroke="#2563EB"
                  strokeWidth={3}
                  dot={{ r: 5 }}
                  activeDot={{ r: 7 }}
                />

              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card glass-morph">
            <h3>Risk Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={riskData}
                  dataKey="value"
                  outerRadius={90}
                >
                  {riskData.map((entry, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ borderRadius: '15px', border: 'none', boxShadow: '0 10px 25px rgba(0,0,0,0.1)' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="risk-legend">
              <div className="legend-item">
                <span className="dot low"></span>
                <span>Low Risk</span>
              </div>
              <div className="legend-item">
                <span className="dot medium"></span>
                <span>Medium Risk</span>
              </div>
              <div className="legend-item">
                <span className="dot high"></span>
                <span>High Risk</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </MainLayout>
  )
}

export default Dashboard