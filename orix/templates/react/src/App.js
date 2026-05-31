import React from 'react';

function App() {
  return (
    <div className="App">
      <h1>Welcome to {{ project_name }}!</h1>
      {% if use_auth %}
      <p>Authentication is enabled.</p>
      {% endif %}
    </div>
  );
}

export default App;
