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
server.get(URL_GATEWAY + "mongo/query/tasks", [
  {'name':'cpu-waster', 'status': 'PENDING', 'issuer': 'Yes', 'start_time': '12/05/2021'}, 
  {'name':'network-stresser', 'status': 'COMPLETE', 'issuer': 'No', 'start_time': '10/03/2021'}, 
  {'name':'mongofill', 'status': 'ERROR', 'issuer': 'Yes', 'start_time': '11/01/2021'}, 
  {"name": "mongoget.py", "status": "RUNNING", "issuer": "?", "start_time": "2021-05-14T03:40:52.681564", "id": "609df14433da60154b4364c1"},
  {"name": "mongoget.py", "status": "FAILURE", "issuer": "?", "start_time": "2021-05-17T17:04:14.750316", "end_time": "2021-05-17T17:29:31.724943", "logs": ["Traceback (most recent call last):", "File \"/worker.py\", line 7, in <module>", "fh.write(json.dumps(client.test.random.find()[0]))", "File \"/usr/local/lib/python3.7/site-packages/pymongo/cursor.py\", line 616, in __getitem__", "raise IndexError(\"no such item for Cursor instance\")", "IndexError: no such item for Cursor instance"], "results": {}, "id": "60a2a20ed92e2ad925f30cd5"}
])
server.post(URL_GATEWAY + "routine")
server.delete("delete")

function App() {

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
        tasksList.push(
          <tr>
            <td>{items[i].name}</td>
            <td>{items[i].status}</td>
            <td>{items[i].start_time}</td>
            <button onClick={() => DownloadTaskLogs(items[i])}>Download logs</button>
            <button onClick={() => DeleteTasks(items[i])}>Delete task</button>
          </tr>);
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
      return(
        <table className="center">
          <tbody>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Start Time</th>
            </tr>
            {renderTasks()}
          </tbody>
        </table>
      ); 
    }
  }

  function DownloadTaskLogs(task){
    
    function download(content, fileName, contentType) {
      const a = document.createElement("a");
      const file = new Blob([content], { type: contentType });
      a.href = URL.createObjectURL(file);
      a.download = fileName;
      a.click();
    }
     
    download(JSON.stringify(task), task.name+"-logs.txt", "text/plain");
  
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

  function DeleteTasks(task) {
      alert('Task ' + task.name + ' has been deleted');
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
      </div>

      <div className="SubmitTasks">
        <h1>Submit Tasks</h1>
          {SubmitTasks()} 
      </div>

    </div>
  );
}

export default App;
