const mongoose = require('mongoose')

const predictionSchema = new mongoose.Schema(
  {
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
      required: true,
      enum: ['Low', 'Medium', 'High']
    },

    confidence: {
      type: String,
      required: true
    },

    severityScore: {
      type: Number
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

    importantFactors: [
      {
        feature: {
          type: String
        },
        impact: {
          type: Number
        }
      }
    ]
  },
  {
    timestamps: true
  }
)

module.exports = mongoose.model('Prediction', predictionSchema)