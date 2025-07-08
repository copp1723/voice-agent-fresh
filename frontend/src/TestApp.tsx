export default function TestApp() {
  return (
    <div style={{ padding: '20px' }}>
      <h1>Voice Agent Dashboard</h1>
      <p>If you can see this, React is working!</p>
      <p>Check browser console for errors.</p>
      <div>
        <h2>Debug Info:</h2>
        <ul>
          <li>Frontend URL: {window.location.href}</li>
          <li>Backend expected at: http://localhost:10000</li>
        </ul>
      </div>
    </div>
  )
}