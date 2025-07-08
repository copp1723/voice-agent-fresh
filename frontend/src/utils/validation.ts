// Validation utilities for forms and data

export const validators = {
  required: (value: any) => {
    if (value === null || value === undefined || value === '') {
      return 'This field is required'
    }
    if (Array.isArray(value) && value.length === 0) {
      return 'Please select at least one item'
    }
    return undefined
  },

  email: (value: string) => {
    if (!value) return undefined
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(value)) {
      return 'Please enter a valid email address'
    }
    return undefined
  },

  phoneNumber: (value: string) => {
    if (!value) return undefined
    // Remove all non-digit characters for validation
    const cleaned = value.replace(/\D/g, '')
    if (cleaned.length !== 10 && cleaned.length !== 11) {
      return 'Please enter a valid phone number'
    }
    return undefined
  },

  minLength: (min: number) => (value: string) => {
    if (!value) return undefined
    if (value.length < min) {
      return `Must be at least ${min} characters`
    }
    return undefined
  },

  maxLength: (max: number) => (value: string) => {
    if (!value) return undefined
    if (value.length > max) {
      return `Must be no more than ${max} characters`
    }
    return undefined
  },

  min: (min: number) => (value: number) => {
    if (value === null || value === undefined) return undefined
    if (value < min) {
      return `Must be at least ${min}`
    }
    return undefined
  },

  max: (max: number) => (value: number) => {
    if (value === null || value === undefined) return undefined
    if (value > max) {
      return `Must be no more than ${max}`
    }
    return undefined
  },

  pattern: (pattern: RegExp, message: string) => (value: string) => {
    if (!value) return undefined
    if (!pattern.test(value)) {
      return message
    }
    return undefined
  },

  url: (value: string) => {
    if (!value) return undefined
    try {
      new URL(value)
      return undefined
    } catch {
      return 'Please enter a valid URL'
    }
  },

  password: (value: string) => {
    if (!value) return undefined
    if (value.length < 8) {
      return 'Password must be at least 8 characters'
    }
    if (!/[A-Z]/.test(value)) {
      return 'Password must contain at least one uppercase letter'
    }
    if (!/[a-z]/.test(value)) {
      return 'Password must contain at least one lowercase letter'
    }
    if (!/[0-9]/.test(value)) {
      return 'Password must contain at least one number'
    }
    return undefined
  },

  confirmPassword: (password: string) => (value: string) => {
    if (!value) return undefined
    if (value !== password) {
      return 'Passwords do not match'
    }
    return undefined
  },

  keywords: (value: string) => {
    if (!value) return undefined
    const keywords = value.split(',').map((k) => k.trim())
    if (keywords.some((k) => k.length === 0)) {
      return 'Keywords cannot be empty'
    }
    if (keywords.some((k) => k.length > 50)) {
      return 'Each keyword must be 50 characters or less'
    }
    return undefined
  },
}

// Compose multiple validators
export const composeValidators = (...validators: Array<(value: any) => string | undefined>) => {
  return (value: any) => {
    for (const validator of validators) {
      const error = validator(value)
      if (error) return error
    }
    return undefined
  }
}

// Validate entire form
export const validateForm = <T extends Record<string, any>>(
  values: T,
  validationRules: Partial<Record<keyof T, (value: any) => string | undefined>>,
): Partial<Record<keyof T, string>> => {
  const errors: Partial<Record<keyof T, string>> = {}
  
  Object.entries(validationRules).forEach(([field, validator]) => {
    if (validator) {
      const error = validator(values[field as keyof T])
      if (error) {
        errors[field as keyof T] = error
      }
    }
  })
  
  return errors
}