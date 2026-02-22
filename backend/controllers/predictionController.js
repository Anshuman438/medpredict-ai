const Prediction = require('../models/Prediction')
const asyncHandler = require('../utils/asyncHandler')
const generateRecommendations = require('../utils/recommendationEngine')
const axios = require('axios')

const analyzeSymptoms = asyncHandler(async (req, res) => {
  const { symptoms } = req.body

  if (!symptoms || symptoms.length === 0) {
    res.status(400)
    throw new Error('No symptoms provided')
  }

  // Call ML microservice
  const mlResponse = await axios.post(
    `${process.env.ML_SERVICE_URL}/predict`,
    { symptoms }
  )

  const { condition, risk, confidence, model_version } = mlResponse.data

  const recommendations = generateRecommendations(condition, risk)

  const savedPrediction = await Prediction.create({
  user: req.user._id,
  symptoms,
  condition,
  risk,
  confidence,
  modelVersion: model_version,
  recommendations
})

  res.status(201).json(savedPrediction)
})

const getUserPredictions = asyncHandler(async (req, res) => {
  const predictions = await Prediction.find({ user: req.user._id })
    .sort({ createdAt: -1 })

  res.json(predictions)
})


module.exports = { analyzeSymptoms, getUserPredictions }