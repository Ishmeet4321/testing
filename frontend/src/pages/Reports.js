import React from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function Reports(){
  const data = {
    labels: ['Week1','Week2','Week3','Week4'],
    datasets: [{ label:'Pronunciation', data:[68,75,82,88], borderColor:'#5b21b6', tension:0.3 }]
  };
  return (
    <div>
      <h1>Reports</h1>
      <div className="card">
        <Line data={data} />
      </div>
    </div>
  );
}
