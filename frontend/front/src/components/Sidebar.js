import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Sidebar(){
  const location = useLocation();
  const links = [
    {name:'Dashboard', to:'/'},
    {name:'Practice', to:'/practice'},
    {name:'Video', to:'/video'},
    {name: 'Assistant', to: '/assistant'},
    {name:'Reports', to:'/reports'},
    {name:'Settings', to:'/settings'},
    //{name:'Emotion-Practice', to:'/emotion-practice'},
  ];
  return (
    <aside className="sidebar">
      <h2>Speech Therapy Assistant</h2>
      {links.map((l)=>(
        <Link key={l.to} to={l.to} style={{fontWeight: location.pathname===l.to?700:500}}>
          {l.name}
        </Link>
      ))}
    </aside>
  );
}
