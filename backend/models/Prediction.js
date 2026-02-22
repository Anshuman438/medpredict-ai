const mongoose = require('mongoose')

const predictionSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    required: true,
    ref: 'User'
  },
  symptoms: {
    type: [String],
    required: true
  },
  condition: {
    type: String,
    required: true
  },
  risk: {
    type: String,
    required: true
  },
  confidence: {
    type: String,
    required: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
    modelVersion: {
    type: String,
    required: true
  },
  recommendations: {
  exercise: [String],
  diet: [String],
  lifestyle: [String]
},
})

module.exports = mongoose.model('Prediction', predictionSchema)