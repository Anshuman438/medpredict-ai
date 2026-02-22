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
  Cell
} from 'recharts'
import { useState, useEffect } from 'react'
import api from '../services/api'

const COLORS = ['#10B981', '#FACC15', '#EF4444']

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

      <div className="dashboard-header">
        <h2>Health Analytics Overview</h2>
        <p>Track your health insights in real time.</p>
      </div>

      <div className="kpi-grid">

        <div className="kpi-card">
          <h4>Total Checks</h4>
          <h2>{totalChecks}</h2>
        </div>

        <div className="kpi-card">
          <h4>High Risk Cases</h4>
          <h2 className="risk-high">{highRisk}</h2>
        </div>

        <div className="kpi-card">
          <h4>Most Common Condition</h4>
          <h2>{mostCommonCondition}</h2>
        </div>

        <div className="kpi-card">
          <h4>Monthly Growth</h4>
          <h2 className="growth">Auto</h2>
        </div>

      </div>

      <div className="analytics-section">

        <div className="chart-card">
          <h3>Monthly Predictions</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={monthlyData}>
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="checks" stroke="#2563EB" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={riskData}
                dataKey="value"
                outerRadius={80}
              >
                {riskData.map((entry, index) => (
                  <Cell key={index} fill={COLORS[index]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

      </div>

    </MainLayout>
  )
}

export default Dashboard