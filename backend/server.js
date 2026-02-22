const express = require('express')
const dotenv = require('dotenv')
const cors = require('cors')
const helmet = require('helmet')
const rateLimit = require('express-rate-limit')
const morgan = require('morgan')

const connectDB = require('./config/db')
const predictionRoutes = require('./routes/predictionRoutes')
const authRoutes = require('./routes/authRoutes')
const { errorHandler } = require('./middleware/errorMiddleware')
const chatRoutes = require('./routes/chatRoutes')
const noteRoutes = require('./routes/noteRoutes')

dotenv.config()

connectDB()

const app = express()

// Core Middleware
app.use(cors())
app.use(express.json())

// Security Middleware
app.use(helmet())

app.use(rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100
}))

// Logging
if (process.env.NODE_ENV === 'development') {
  app.use(morgan('dev'))
}

// Health Route
app.get('/', (req, res) => {
  res.json({ message: 'MedPredict AI Backend Running' })
})

// API Routes
app.use('/api/auth', authRoutes)
app.use('/api/predictions', predictionRoutes)
app.use('/api/chat', chatRoutes)
app.use('/api/notes', noteRoutes)

// Global Error Handler
app.use(errorHandler)

const PORT = process.env.PORT || 5000

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`)
})