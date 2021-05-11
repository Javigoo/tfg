import './App.css';
import React from 'react';

function App() {

  function downloadButton() {
    alert("downloadButton");
  }

  return (
    <div className="App">

      <div className="Login">
        <h1>Login</h1>
          <p>
            Login usuario, para hacer las llamadas filtrando las tareas por el usuario al que pertenecen
          </p>
      </div>

      <div className="ListTasks">
        <h1>List Tasks</h1>
          <p>
            Listar tareas y para cada tarea información de la misma en función de su estado (Pending, complete, error, etc) 
          </p>
          <p>
            Botón para descargar resultados (log)
          </p>
        <button onClick={downloadButton}> Download results </button>

      </div>

      <div className="SubmitTasks">
        <h1>Submit Tasks</h1>
          <p>
            Form to submit tareas          
          </p>

      </div>

      <div className="DeleteTasks">
        <h1>Delete Tasks</h1>
          <p>
            Eliminar tareas, form para seleccionar cual eliminar          
          </p>

      </div>

    </div>
  );
}

export default App;
