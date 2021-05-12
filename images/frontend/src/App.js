import './App.css';
import React, { useEffect, useState } from 'react';

import LoginButton from './components/LoginButton';
import LogoutButton from './components/LogoutButton';
import Profile from './components/Profile';
import { useAuth0 } from '@auth0/auth0-react';

import { createServer } from 'miragejs';
import axios from 'axios';

const URL_GATEWAY = 'http://192.168.101.70:5000/'

// Fake backend
let server = createServer()
server.get(URL_GATEWAY + "mongo/query/tasks", [{'name':'cpu-waster', 'status': 'PENDING', 'issuer': 'Yes', 'start_time': '12/05/2021'}, {'name':'network-stresser', 'status': 'COMPLETE', 'issuer': 'No', 'start_time': '10/03/2021'}, {'name':'mongofill', 'status': 'ERROR', 'issuer': 'Yes', 'start_time': '11/01/2021'}])
server.post(URL_GATEWAY + "routine")
server.delete("delete")

function App() {
  var tasks = []

  function Login() {
    const { isLoading } = useAuth0();

    if (isLoading) return <div>Loading...</div>

    return (
      <>
        <LoginButton />
        <LogoutButton />
        <Profile />
      </>
    );
  }


  function ShowTasks() {
    const [error, setError] = useState(null);
    const [isLoaded, setIsLoaded] = useState(false);
    const [items, setitems] = useState([]);

    function renderTasks() {
      const tasksList = [];
      for(let i = 0; i < items.length; i++) {
        tasksList.push(<tr><td>{items[i].name}</td><td>{items[i].status}</td><td>{items[i].issuer}</td><td>{items[i].start_time}</td></tr>);
      }

      return tasksList;
    }

    useEffect(() => {
      fetch(URL_GATEWAY + "mongo/query/tasks")
        .then(res => res.json())
        .then(
          (result) => {
            setIsLoaded(true);
            setitems(result);
          },

          (error) => {
            setIsLoaded(true);
            setError(error);
          }
        )
    }, [])

    if (error) {
      return <div> Error: {error.message} </div>;
    } else if (!isLoaded) {
      return <div>  Loading ... </div>;
    } else {
      tasks = items;
      return(
        <table className="center">
          <tbody>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>IsUser</th>
              <th>Start Time</th>
            </tr>
            {renderTasks()}
          </tbody>
        </table>
      ); 
    }
  }

  function DownloadTaskLogs(){
     
    function download(content, fileName, contentType) {
      const a = document.createElement("a");
      const file = new Blob([content], { type: contentType });
      a.href = URL.createObjectURL(file);
      a.download = fileName;
      a.click();
    }
     
    download(JSON.stringify(tasks), "task-logs.txt", "text/plain");
  
  }

  function SubmitTasks() {
    const [programFile, setProgramFile] = useState(null);
    const [requirementsFile, setRequirementsFile] = useState(null);
  
    const submitForm = () => {
      const formData = new FormData();
      formData.append("program", programFile);
      formData.append("requirements", requirementsFile);

      axios
        .post(URL_GATEWAY + "routine", formData)
        .then((res) => {
          alert("File Upload success");
        })
        .catch((err) => alert("File Upload Error"));
    };

    const FileUploader = ({onFileSelect}) => {  
      const handleFileInput = (e) => {
          onFileSelect(e.target.files[0])
      }
  
      return (
          <div className="file-uploader">
            <input type="file" onChange={handleFileInput}></input>
          </div>
      )
    }

    return (
      <form>
        Select a file with the program:
        <FileUploader
          onFileSelectSuccess={(file) => setProgramFile(file)}
          onFileSelectError={({error}) => alert(error)}
        />
        <br></br>
        Select a file with the requirements:
        <FileUploader
          onFileSelectSuccess={(file) => setRequirementsFile(file)}
          onFileSelectError={({error}) => alert(error)}
        />
        <br></br>
        <button onClick={submitForm}>Submit</button>
      </form>
    );
  }

  function DeleteTasks() {
    const [task, setTask] = useState(null);
    
    function renderTasks() {
      const tasksList = [];
      for(let i = 0; i < tasks.length; i++) {
        tasksList.push(<option value={tasks[i].name}>{tasks[i].name}</option>);
      }

      return tasksList;
    }

    function handleChange(event) {
      setTask(event.target.value);
    }
  
    function handleSubmit(event) {
      fetch('delete', { method: 'DELETE' });
      alert('Task ' + task + ' has been deleted');
      event.preventDefault();
    }

    return (
      <form onSubmit={handleSubmit}>
        Select the task you want to delete:
        <br></br>
        <label>
          <br></br>
          <select value={task} onChange={handleChange}>
            {renderTasks()}
          </select>
        </label>
        <input type="submit" value="Submit" />
      </form>
    )
  }

  return (
    <div className="App">

      <div className="Login">
        <h1>Login</h1>
          {Login()}
      </div>

      <div className="ListTasks">
        <h1>List Tasks</h1>
          {ShowTasks()}
          <br></br>
          <button onClick={DownloadTaskLogs}>Download</button>
      </div>

      <div className="SubmitTasks">
        <h1>Submit Tasks</h1>
          {SubmitTasks()} 
      </div>

      <div className="DeleteTasks">
        <h1>Delete Tasks</h1>
          {DeleteTasks()}
      </div>

    </div>
  );
}

export default App;
