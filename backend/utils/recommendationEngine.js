const generateRecommendations = (condition, risk) => {
  let exercise = []
  let diet = []
  let lifestyle = []

  if (String(condition).toLowerCase().includes('inconclusive')) {
    return {
      exercise: [
        'Avoid strenuous activity until symptoms are clearer',
        'Take rest and monitor symptom progression'
      ],
      diet: [
        'Keep hydration high (water/electrolytes)',
        'Prefer light, easily digestible meals'
      ],
      lifestyle: [
        'Track additional symptoms for the next 12-24 hours',
        'Retake analysis with more symptom details',
        'Seek clinical evaluation if symptoms worsen'
      ]
    }
  }

  if (risk === 'High') {
    exercise = [
      'Light walking (20 mins daily)',
      'Breathing exercises',
      'Avoid intense workouts'
    ]

    diet = [
      'Low sodium diet',
      'Increase leafy vegetables',
      'Avoid processed food'
    ]

    lifestyle = [
      'Monitor blood pressure regularly',
      'Reduce stress levels',
      'Ensure 7-8 hours sleep'
    ]
  }

  if (risk === 'Medium') {
    exercise = [
      'Moderate cardio (30 mins)',
      'Stretching routine',
      'Yoga'
    ]

    diet = [
      'Balanced protein intake',
      'Reduce sugar',
      'Hydration 2-3L daily'
    ]

    lifestyle = [
      'Maintain consistent sleep schedule',
      'Weekly health monitoring'
    ]
  }

  if (risk === 'Low') {
    exercise = [
      'Regular jogging',
      'Strength training',
      'Outdoor activities'
    ]

    diet = [
      'Balanced diet',
      'Fruits daily',
      'Maintain hydration'
    ]

    lifestyle = [
      'Maintain healthy routine',
      'Quarterly checkups'
    ]
  }

  return { exercise, diet, lifestyle }
}

module.exports = generateRecommendations