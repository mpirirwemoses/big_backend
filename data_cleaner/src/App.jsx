import { useState } from 'react'

import Auth from './assets/Components/Signup'
import Home from './assets/Components/Home'
import './App.css'

function App() {
  

 const [user, setUser] = useState(null);

  return (
    <>
      {user ? (
        <Home user={user} setUser={setUser} />
      ) : (
        <Auth setUser={setUser} />
      )}
    </>
  )
}

export default App
