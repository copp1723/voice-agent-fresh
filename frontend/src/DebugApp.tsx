import { useState } from 'react'

export default function DebugApp() {
  const [error, setError] = useState<string>('')
  
  const testImports = async () => {
    try {
      // Test each import one by one
      const tests = [
        { name: 'React Router', fn: () => import('react-router-dom') },
        { name: 'MUI', fn: () => import('@mui/material') },
        { name: 'Store', fn: () => import('./store/index') },
        { name: 'App Router', fn: () => import('./AppRouter') },
      ]
      
      for (const test of tests) {
        try {
          await test.fn()
          console.log(`✅ ${test.name} loaded`)
        } catch (e) {
          const msg = `❌ ${test.name} failed: ${e}`
          console.error(msg)
          setError(prev => prev + '\n' + msg)
        }
      }
    } catch (e) {
      console.error('Test failed:', e)
    }
  }
  
  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>Debug App</h1>
      <button onClick={testImports}>Test Imports</button>
      <pre>{error}</pre>
      <hr />
      <h2>Basic Navigation Test</h2>
      <div>
        <a href="/login" style={{ marginRight: '10px' }}>Go to /login</a>
        <a href="/dashboard">Go to /dashboard</a>
      </div>
    </div>
  )
}