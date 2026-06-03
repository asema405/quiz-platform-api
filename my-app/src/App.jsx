import { useEffect, useState } from 'react';
import axios from 'axios';

function App() {
  const [data, setData] = useState([]);

  // API'ден маалыматты алуу
  useEffect(() => {
    axios.get('https://asema405.pythonanywhere.com/api/ВАШ_ЭНДПОИНТ/') // Өзүңдүн эндпоинтиңди кой
      .then(response => {
        setData(response.data);
      })
      .catch(error => {
        console.error("API менен байланышта ката кетти:", error);
      });
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>Менин API маалыматтарым</h1>
      <ul>
        {data.map((item, index) => (
          <li key={index}>{item.name}</li> // Бул жерде API'ден келген талаанын атын жаз
        ))}
      </ul>
    </div>
  );
}

export default App;