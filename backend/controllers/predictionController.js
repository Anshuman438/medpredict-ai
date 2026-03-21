const Prediction = require('../models/Prediction')
const asyncHandler = require('../utils/asyncHandler')
const generateRecommendations = require('../utils/recommendationEngine')
const axios = require('axios')

const DEFAULT_ML_SERVICE_URL = 'http://127.0.0.1:8000'

const normalizeSymptomForModel = (value) =>
  String(value || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '_')

const inferRiskFromConfidence = (confidence) => {
  if (typeof confidence !== 'number' || Number.isNaN(confidence)) return 'Low'
  if (confidence >= 0.7) return 'High'
  if (confidence >= 0.4) return 'Medium'
  return 'Low'
}

const analyzeSymptoms = asyncHandler(async (req, res) => {
  const { symptoms } = req.body

  if (!symptoms || symptoms.length === 0) {
    res.status(400)
    throw new Error('No symptoms provided')
  }

  const normalizedSymptoms = symptoms.map(normalizeSymptomForModel)

  let mlResponse
  try {
    mlResponse = await axios.post(
      `${process.env.ML_SERVICE_URL || DEFAULT_ML_SERVICE_URL}/predict`,
      { symptoms: normalizedSymptoms }
    )
  } catch (error) {
    res.status(502)
    throw new Error(
      error?.response?.data?.error ||
      error?.response?.data?.message ||
      'ML service unavailable. Start ml-service and verify ML_SERVICE_URL.'
    )
  }

  const {
    condition,
    confidence,
    severity_score,
    important_factors,
    model_version,
  } = mlResponse.data

  const safeConfidence =
    typeof confidence === 'number' && !Number.isNaN(confidence)
      ? confidence
      : 0

  const safeRisk =
    typeof mlResponse.data.risk === 'string' && ['Low', 'Medium', 'High'].includes(mlResponse.data.risk)
      ? mlResponse.data.risk
      : inferRiskFromConfidence(safeConfidence)

  const safeSeverityScore =
    typeof severity_score === 'number' && !Number.isNaN(severity_score)
      ? severity_score
      : Math.max(1, Math.min(5, Math.ceil(normalizedSymptoms.length / 3)))

  const safeModelVersion = model_version || 'custom_v1'

  const safeImportantFactors = Array.isArray(important_factors)
    ? important_factors
    : normalizedSymptoms.slice(0, 3)

  const safeCondition = condition || 'Inconclusive - add more symptoms'

  const recommendations = generateRecommendations(safeCondition, safeRisk)

  const savedPrediction = await Prediction.create({
  user: req.user._id,
  symptoms,
  condition: safeCondition,
  risk: safeRisk,
  confidence: safeConfidence,
  severityScore: safeSeverityScore,
  modelVersion: safeModelVersion,
  importantFactors: safeImportantFactors.map(symptom => ({
    feature: symptom,
    impact: 1
  })),
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